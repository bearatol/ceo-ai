"""Original stdlib-only lexical observations of an already captured snapshot.

This module never opens bundle resources, follows references, executes content,
reads environment variables, or contacts a service. Complete coverage means all
admitted text was processed by these rules, not complete threat detection.
Capability and risk are independent heuristics; neither establishes trust.
"""
import bisect
import hashlib
import json
import pathlib
import re
import unicodedata
from urllib.parse import unquote, urlsplit

ENGINE = "ceo-local-static"
ENGINE_VERSION = "1.1.0"
MAX_FILE = 256 * 1024
MAX_TOTAL = 16 * 1024 * 1024
MAX_ANALYSIS_BYTES = 1024 * 1024
MAX_COUNT = 1024
MAX_LINES = 8192
MAX_LINE = 8192
MAX_FINDINGS = 256
MAX_REASONS = 128
MAX_REFERENCES = 256
EXCLUSION_REASONS = ("sensitive-resource", "excluded-resource", "oversized-resource")
TEXT_SUFFIXES = (".md", ".txt", ".rst", ".json", ".csv")
CODE_SUFFIXES = (".py", ".sh", ".bash", ".zsh", ".js", ".mjs", ".ts", ".tsx", ".jsx", ".go", ".rb", ".pl", ".ps1", ".bat", ".c", ".cpp")
SEVERITIES = ("NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL")

# Bounded distances avoid unbounded backtracking and permit wrapped prose.
SECRET = r"(?:secret\w*|credential\w*|private|api[ -]?(?:key|token)|access[ -]?key|token\w*|\.env\b|секрет\w*|приватн\w*|ключ\w*|токен\w*)"
SEND = r"(?:send|upload|post|transmit|transfer|forward|exfiltrate|отправь|отправляй|отправить|отправлять|передай|передать|передавай)"
DELEGATE = r"(?:sub[ -]?agents?|another assistant|other assistant|helper agent|delegat\w*|друг\w*\s+агент\w*|субагент\w*|делегир\w*)"
APPROVAL_EVASION = r"\b(?:bypass|skip|disable)\s+(?:(?:the|any|all|mandatory|user)\s+){0,2}(?:approval|permission|security|safety)\b(?:\s+(?:checks?|requirements?|gates?))?"
EVASION = (r"(?:\bwithout\s+(?:the\s+)?(?:approval|permission)\b|" + APPROVAL_EVASION
           + r"|\b(?:conceal|hide)\b[^;.!?\n]{0,100}\b(?:delegation|handoff|from\s+(?:the\s+)?user)\b"
             r"|\bomit\s+(?:the\s+)?restrictions\b|не\s+передавай\s+ограничения"
             r"|(?:скрой|скрывай)[^;.!?\n]{0,100}(?:делегир\w*|от\s+пользователя)"
             r"|обойди\s+проверк\w*\s+разрешени\w*|без\s+(?:разрешения|согласования))")
SHELL_PIPE = r"\b(?:curl|wget)\b[^\n;]{0,350}\|\s*(?:ba|z|k)?sh\b"
EXECUTABLE_FETCH = (
    r"\b(?:download|fetch)\s+(?:(?:the|a|an|remote|external|helper|shell|python|javascript)\s+){0,4}"
    r"(?:script|code|executable|binary|installer|payload)\b[^;!?]{0,160}?"
    r"\b(?:execute|run)\s+(?:(?:the|this|that|downloaded|fetched)\s+){0,3}"
    r"(?:it|them|script|code|executable|binary|installer|payload|contents)\b"
    r"|(?:скачай|загрузи)\s+(?:(?:внешний|удал[её]нный|этот)\s+){0,2}"
    r"(?:скрипт|код|исполняемый\s+файл)[^;.!?]{0,160}?(?:выполни|запусти)\s+(?:его|их|скрипт|код)\b"
)
INDIRECT_DATA = (r"\b(?:its|their|the|these|those)\s+(?:(?:complete|full|entire|private)\s+){0,2}(?:contents?|file|data)\b"
                 r"|(?:его|их|полное|вс[её])\s+(?:содержим\w*|данные|файл\w*)"
                 r"|содержим\w*\s+файл\w*")
RULES = (
    ("PROMPT_OVERRIDE", "HIGH", r"(?:ignore|disregard|override|bypass)\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|original|system|developer|higher[ -]priority)(?:\s+(?:system|developer|and)){0,4}\s+(?:instructions?|rules?|restrictions?|messages?)|(?:игнорируй|проигнорируй|игнорировать|обойди)\s+(?:все\s+)?(?:прежние|предыдущие|системные|исходные)\s+(?:инструкции|правила|ограничения)"),
    ("EXFILTRATION", "HIGH", r"\b" + SEND + r"\b"),
    ("RUNTIME_CODE_ACQUISITION", "CRITICAL", SHELL_PIPE + "|" + EXECUTABLE_FETCH),
    ("ENCODED_EXECUTION", "HIGH", r"\b(?:exec|eval)\s*\(\s*(?:base64|b64decode|bytes\.fromhex)|\bbase64\s+(?:--decode|-d)[^\n]{0,160}\|\s*(?:bash|sh|python)\b"),
    ("DESTRUCTIVE_COMMAND", "HIGH", r"\brm\s+-[a-z]*r[a-z]*f[a-z]*\s+(?:/|~|\*)|\b(?:delete|destroy|wipe)\s+all\s+(?:local\s+)?files\b|(?:удали|уничтожь)\s+все\s+файлы"),
    ("PERSISTENCE_CHANGE", "HIGH", r"\bcrontab\s+(?:-|[^\s]+\.(?:txt|cron))|\b(?:install|add|write|create)\b[^\n]{0,100}\b(?:cron\s*job|launchagent|startup\s+(?:entry|script))\b|(?:создай|добавь)[^\n]{0,100}(?:автозапуск|задание\s+cron)"),
    ("COVERT_DELEGATION", "HIGH", EVASION),
    ("APPROVAL_BYPASS", "HIGH", APPROVAL_EVASION + r"|\b(?:do not|don't|never)\s+(?:ask|request|seek)\s+(?:for\s+)?(?:user\s+)?(?:approval|permission)\b|не\s+(?:запрашивай|спрашивай)\s+разрешени\w*|обойди\s+проверк\w*\s+разрешени\w*"),
    ("CONCEALED_ACTION", "MEDIUM", r"\b(?:hide|conceal)\b[^;.!?]{0,120}?\bfrom\s+(?:the\s+)?user\b|(?:скрой|скрывай)[^;.!?]{0,100}?от\s+пользователя|не\s+сообщай\s+(?:ему|пользователю)"),
    ("CREDENTIAL_URL_TEMPLATE", "LOW", r"\bhttps?://[^\s'\"<>]{1,400}[?&](?:(?:api[_-]?key|access[_-]?token|auth[_-]?token|token|secret|password)=(?:\{|\$|<|[A-Za-z0-9_])|key=\$\{(?:key|api_?key)\})"),
    ("CLI_API_KEY_ARGUMENT", "LOW", r"\b(?:add_argument|add_option|option)\s*\(\s*['\"]--api-key['\"]|(?<!\w)--api-key(?:\s+<[^>\n]{1,80}>|=\$\{?[A-Za-z_]\w{0,60})"),
)
CAPABILITIES = (
    (1, r"\b(?:read|write|open|save)\b[^\n]{0,70}\b(?:local\s+)?(?:file|report)\b|\b(?:scripts?/|python3?\s|bash\s)|(?:прочитай|запиши|открой)[^\n]{0,70}(?:файл|отч[её]т)"),
    (2, r"\b(?:https?://|curl\b|wget\b|http\s+client|outbound|network|remote\s+server)|(?:сетев\w*|внешний\s+сервер)|" + SEND),
    (3, SECRET + r"|\b(?:sudo|crontab|launchagents?|privilege|persistence)\b|\brm\s+-|(?:автозапуск|привилеги\w*)"),
    (4, r"\b(?:exec|eval)\s*\(|" + SHELL_PIPE + "|" + EXECUTABLE_FETCH + r"|\bbase64\s+(?:--decode|-d)[^\n]{0,160}\|"),
)
API_POLICY = {"enabled": False, "implemented": False,
              "requires": ["explicit-opt-in", "data-approval", "hard-budget"]}
POLICY = {"max_file": MAX_FILE, "max_total": MAX_TOTAL, "max_count": MAX_COUNT,
          "max_analysis_bytes": MAX_ANALYSIS_BYTES,
          "max_lines": MAX_LINES, "max_line": MAX_LINE,
          "max_findings": MAX_FINDINGS, "max_reasons": MAX_REASONS,
          "max_references": MAX_REFERENCES, "text_suffixes": TEXT_SUFFIXES,
          "exclusion_reasons": EXCLUSION_REASONS,
          "code_suffixes": CODE_SUFFIXES, "api": API_POLICY,
          "script_minimum_tier": "T1", "partial_capability": "explicit-lower-bound-or-unknown",
          "trust": "unverified", "coverage": "bounded-lexical-no-ast-or-runtime-assurance"}


def _json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


# The only file read is this trusted installed scanner's own source identity.
with open(__file__, "rb") as _source:
    _scanner_source = _source.read(1024 * 1024 + 1)
if len(_scanner_source) > 1024 * 1024:
    raise ValueError("scanner source exceeds identity limit")
SCANNER_SHA256 = hashlib.sha256(_scanner_source).hexdigest()
del _scanner_source
RULES_SHA256 = _json_digest({"risks": RULES, "capabilities": CAPABILITIES,
                            "sensitive_target": SECRET, "indirect_target": INDIRECT_DATA, "delegate_context": DELEGATE})
POLICY_SHA256 = _json_digest(POLICY)
IDENTITY_SHA256 = _json_digest([ENGINE, ENGINE_VERSION, SCANNER_SHA256, RULES_SHA256, POLICY_SHA256])
_RULE_PATTERNS = tuple((name, severity, re.compile(pattern, re.I)) for name, severity, pattern in RULES)
_CAP_PATTERNS = tuple((tier, re.compile(pattern, re.I)) for tier, pattern in CAPABILITIES)
_MARKDOWN_LINK = re.compile(r"\[[^\]\n]{0,500}\]\(\s*<?([^\s)>]{1,2048})")
_BARE_URL = re.compile(r"\b(?:https?|ftp|wss?)://[^\s<>]{1,2048}", re.I)
_BACKTICK_PATH = re.compile(r"`((?:\.{0,2}/|references/|scripts/|resources/|assets/)[^`\n]{1,1024})`")
_BARE_LOCAL_PATH = re.compile(r"(?<![\w:/])((?:~/|/|\.{1,2}/|references/|scripts/|resources/|assets/)[^\s<>`'\"()\[\]]{1,1024})")
_NEGATED = re.compile(r"(?:\bnever|\bdo not|\bdon't|\bmust not|\bне|\bнельзя)\s+(?:ever\s+)?$", re.I)
_COORDINATED_NEGATION = re.compile(r"\b(?:never|do not|don't|must not)\b[^;.!?\n\"'`«»“”]{0,100}\b(?:or|nor)\s+$", re.I)
_NEGATED_COMMAND = re.compile(r"(?:\b(?:never|do not|don't|must not)\s+(?:run|execute)|\bне\s+(?:запускай|выполняй))\s+[`'\"]?\s*$", re.I)
_SHELL_PIPE_ACTION = re.compile(r"(?:curl|wget)\b", re.I)
_SENSITIVE_TARGET = re.compile(SECRET, re.I)
_FORBIDDEN_TARGET = re.compile(r"\s+no\s+" + SECRET, re.I)
_INDIRECT_TARGET = re.compile(INDIRECT_DATA, re.I)
_SEND_ACTION = re.compile(r"\b" + SEND + r"\b", re.I)
_DELEGATE_CONTEXT = re.compile(DELEGATE, re.I)
_CLAUSE_END = re.compile(r"[;!?]|\.(?:\s|$)|\b(?:but|however|instead|затем|однако|но)\b", re.I)
_TRANSFER_BLOCK_END = re.compile(r"\r?\n[ \t]*\r?\n|\r?\n[ \t]*(?:[-+*]|\d{1,6}[.)])[ \t]+")
_INLINE_QUOTES = re.compile(r'(?<!\w)([\"\'`])[^\n]{0,600}?\1|“[^”\n]{0,600}”|«[^»\n]{0,600}»')


def disabled_api_contract():
    """A future interface contract only; there is no client or activation path."""
    return {"enabled": False, "implemented": False,
            "requires": ["explicit-opt-in", "data-approval", "hard-budget"]}


def _validate_path(path):
    if (not isinstance(path, str) or not path or len(path) > 1024
            or "\\" in path or any(part in ("", ".", "..") for part in path.split("/"))
            or any(unicodedata.category(char).startswith("C") for char in path)
            or unicodedata.normalize("NFC", path) != path):
        raise ValueError("noncanonical bundle path")
    if len(path.encode("utf-8")) > 1024 or re.match(r"^[A-Za-z]:", path):
        raise ValueError("noncanonical bundle path")


def _validate_files(files):
    if type(files) is not dict or len(files) > MAX_COUNT:
        raise ValueError("invalid bundle mapping or entry limit")
    total = 0
    for path, raw in files.items():
        _validate_path(path)
        if type(raw) is not bytes or len(raw) > MAX_FILE:
            raise ValueError("invalid bundle bytes or file limit")
        total += len(raw)
        if total > MAX_TOTAL:
            raise ValueError("bundle byte limit")


def bundle_digest(files):
    """Hash canonical path and byte frames, including hidden/nested resources."""
    _validate_files(files)
    digest = hashlib.sha256(b"ceo-ai-bundle-v1\0")
    for path in sorted(files):
        encoded, raw = path.encode("utf-8"), files[path]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def _reference_reason(target, path, files, kind):
    try:
        target = unquote(target)
        parsed = urlsplit(target)
    except ValueError:
        return "unsupported-reference"
    if parsed.scheme or parsed.netloc:
        return "external-reference"
    if not parsed.path:
        return None
    if kind == "agent":
        return "agent-reference-not-followed"
    if target.startswith(("/", "~")) or "\\" in target:
        return "out-of-package-reference"
    parts = path.split("/")[:-1]
    for part in parsed.path.split("/"):
        if part == "..":
            if not parts:
                return "out-of-package-reference"
            parts.pop()
        elif part not in ("", "."):
            parts.append(part)
    resolved = "/".join(parts)
    return None if resolved in files else "missing-reference"


def _qualified(rule_id, match, text):
    """Require nearby evidence about the action, never a file/role allowlist."""
    if rule_id == "COVERT_DELEGATION":
        return bool(_DELEGATE_CONTEXT.search(text[max(0, match.start() - 600):match.end()]))
    if rule_id == "EXFILTRATION":
        following = text[match.end():match.end() + 300]
        boundary = _CLAUSE_END.search(following)
        target = following[:boundary.start()] if boundary else following
        block_end = _TRANSFER_BLOCK_END.search(target)
        if block_end:
            target = target[:block_end.start()]
        next_action = _SEND_ACTION.search(target)
        if next_action:
            target = target[:next_action.start()]
        if _SENSITIVE_TARGET.search(target):
            return True
        # Generic content is not sensitive. Pronouns require a local sensitive
        # antecedent; this limited association is still only a lexical signal.
        return bool(_INDIRECT_TARGET.search(target) and
                    _SENSITIVE_TARGET.search(text[max(0, match.start() - 300):match.start()]))
    return True


def _uncertain(text, start, end, offsets, lines, *, executable_command=False):
    first = bisect.bisect_right(offsets, start) - 1
    last = bisect.bisect_right(offsets, max(start, end - 1)) - 1
    # Only quote the actual matched action. Nearby examples, paragraphs, and
    # fences cannot downgrade a separate instruction outside their quotation.
    if all(lines[index].lstrip().startswith(">") for index in range(first, last + 1)):
        return True
    local_start = max(offsets[first], start - 600)
    local_end = min(len(text), end + 600, offsets[last] + len(lines[last]))
    for quote in _INLINE_QUOTES.finditer(text[local_start:local_end]):
        if executable_command and quote[0].startswith("`"):
            # Inline code formatting is also used to instruct installation.
            # It is not evidence that an explicit command is merely quoted.
            continue
        if local_start + quote.start() < start and end < local_start + quote.end():
            return True
    prefix = text[max(0, start - 150):start]
    return bool(_NEGATED.search(prefix) or _COORDINATED_NEGATION.search(prefix)
                or (executable_command and _NEGATED_COMMAND.search(prefix)))


def analyze_bundle(files, *, kind="skill", excluded=()):
    """Return deterministic, bounded observations without reading any resource.

    Exclusions are supplied by the safe reader; their bytes never enter this
    function. A full bundle hash is unavailable when any resource was excluded.
    Malformed snapshot inputs raise ValueError without echoing their content.
    """
    _validate_files(files)
    if kind not in ("skill", "agent") or (kind == "agent" and len(files) > 1):
        raise ValueError("invalid component kind or agent file scope")
    if not isinstance(excluded, (list, tuple)) or len(files) + len(excluded) > MAX_COUNT:
        raise ValueError("invalid exclusion list or entry limit")
    seen_excluded = set()
    for item in excluded:
        if type(item) is not dict or set(item) != {"path", "reason"} or item["reason"] not in EXCLUSION_REASONS:
            raise ValueError("invalid exclusion record")
        _validate_path(item["path"])
        if item["path"] in files or item["path"] in seen_excluded:
            raise ValueError("duplicate or admitted exclusion")
        seen_excluded.add(item["path"])

    reasons, findings, finding_keys = [], [], set()
    reason_keys = set()
    highest_tier, analyzed, analysis_bytes = None, 0, 0

    def reason(code, path=None):
        key = (code, path)
        if key in reason_keys:
            return
        reason_keys.add(key)
        if len(reasons) < MAX_REASONS - 1:
            reasons.append({"reason": code, **({"path": path} if path else {})})
        elif not any(item["reason"] == "coverage-reason-limit" for item in reasons):
            reasons.append({"reason": "coverage-reason-limit"})

    for item in sorted(excluded, key=lambda item: item["path"]):
        reason(item["reason"], item["path"])
    if not files:
        reason("empty-bundle")
    for path, raw in sorted(files.items()):
        # Lexical matching has a separate deterministic work budget. Every
        # observed byte is still hashed, even when its analysis is skipped.
        if analysis_bytes + len(raw) > MAX_ANALYSIS_BYTES:
            reason("analysis-byte-limit", path)
            continue
        analysis_bytes += len(raw)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            reason("binary-or-unparseable", path)
            continue
        if any(ord(char) < 32 and char not in "\n\r\t" for char in text):
            reason("binary-or-unparseable", path)
            continue
        suffix = pathlib.PurePosixPath(path).suffix.lower()
        if suffix not in TEXT_SUFFIXES:
            reason("unsupported-code-lexical-only" if suffix in CODE_SUFFIXES else "unsupported-type-lexical-only", path)
        if suffix == ".json":
            try:
                json.loads(text)
            except (ValueError, RecursionError):
                reason("unparseable-structured-text", path)
        lines = text.splitlines(keepends=True)
        if len(lines) > MAX_LINES or any(len(line) > MAX_LINE for line in lines):
            reason("text-analysis-limit", path)
            continue
        offsets, offset = [], 0
        for line in lines:
            offsets.append(offset)
            offset += len(line)
        highest_tier = max(highest_tier or 0, 1 if suffix in CODE_SUFFIXES else 0)
        for tier, pattern in _CAP_PATTERNS:
            if pattern.search(text):
                highest_tier = max(highest_tier, tier)
        analyzed += 1
        for rule_id, severity, pattern in _RULE_PATTERNS:
            for match in pattern.finditer(text):
                if not _qualified(rule_id, match, text):
                    continue
                line_number = bisect.bisect_right(offsets, match.start())
                executable_command = rule_id == "ENCODED_EXECUTION" or (
                    rule_id == "RUNTIME_CODE_ACQUISITION" and bool(_SHELL_PIPE_ACTION.match(match[0])))
                uncertain = severity != "LOW" and _uncertain(
                    text, match.start(), match.end(), offsets, lines, executable_command=executable_command)
                if rule_id == "EXFILTRATION" and _FORBIDDEN_TARGET.match(text[match.end():match.end() + 80]):
                    uncertain = True
                current_rule, current_severity = ("CONTEXT_UNCERTAIN", "LOW") if uncertain else (rule_id, severity)
                key = (path, line_number, current_rule)
                if key in finding_keys:
                    continue
                if len(findings) >= MAX_FINDINGS:
                    reason("finding-limit", path)
                    break
                finding_keys.add(key)
                findings.append({"rule_id": current_rule, "severity": current_severity,
                                 "path": path, "line": line_number})
        reference_count = 0
        for pattern in (_MARKDOWN_LINK, _BARE_URL, _BACKTICK_PATH, _BARE_LOCAL_PATH):
            for match in pattern.finditer(text):
                reference_count += 1
                if reference_count > MAX_REFERENCES:
                    reason("reference-limit", path)
                    break
                target = match[1] if pattern is not _BARE_URL else match[0]
                if pattern is _BARE_LOCAL_PATH:
                    target = target.rstrip(".,;:")
                code = _reference_reason(target, path, files, kind)
                if code:
                    reason(code, path)
            if reference_count > MAX_REFERENCES:
                break

    findings.sort(key=lambda item: (item["path"], item["line"], item["rule_id"]))
    reasons.sort(key=lambda item: (item.get("path", ""), item["reason"]))
    severity = max((item["severity"] for item in findings), key=SEVERITIES.index, default="NONE")
    observed_digest = bundle_digest(files)
    # Incomplete observation cannot establish that a bundle is text-only.
    observed_tier = None if highest_tier is None or (highest_tier == 0 and reasons) else f"T{highest_tier}"
    capability = {"observed_tier": observed_tier, "basis": "heuristic"}
    if reasons and observed_tier is not None:
        capability["lower_bound"] = True
    return {
        "engine": ENGINE, "engine_version": ENGINE_VERSION,
        "scanner_sha256": SCANNER_SHA256, "rules_sha256": RULES_SHA256,
        "policy_sha256": POLICY_SHA256, "identity_sha256": IDENTITY_SHA256,
        "bundle_sha256": None if excluded else observed_digest,
        "observed_bundle_sha256": observed_digest,
        "source": {"type": "local", "verified": False}, "trust": "unverified",
        "capability": capability,
        "severity": severity, "findings": findings,
        "coverage": {"status": "partial" if reasons else "complete",
                     "scope": "agent-file-only" if kind == "agent" else "admitted-bundle-text",
                     "method": "lexical-rules-no-ast-or-runtime-assurance",
                     "files_received": len(files), "files_analyzed": analyzed,
                     "analysis_bytes": analysis_bytes, "analysis_byte_limit": MAX_ANALYSIS_BYTES,
                     "reasons": reasons},
        "decision": "incomplete" if reasons else "review-required" if findings else "no-findings",
        "semantic_api": disabled_api_contract(),
    }
