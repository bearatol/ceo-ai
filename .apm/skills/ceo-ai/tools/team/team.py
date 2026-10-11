#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def catalog_path(home):
    candidates = [home / "catalog.json", home / "catalog" / "catalog.json"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    fail(f"catalog not found under {home}")


def load_catalog(home):
    path = catalog_path(home)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read catalog: {exc}")
    component_map(data)
    return data, path


def component_map(catalog):
    if not isinstance(catalog, dict) or not isinstance(catalog.get("components"), list):
        fail("catalog components must be an array")
    result = {}
    for item in catalog["components"]:
        if not isinstance(item, dict):
            fail("catalog component must be an object")
        identity = item.get("id")
        kind = item.get("type")
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z]+:[a-z0-9][a-z0-9-]*", identity):
            fail("invalid catalog identity")
        if kind not in ("agent", "skill", "rule", "tool", "orchestration", "model") or identity.split(":", 1)[0] != kind:
            fail("invalid catalog component type")
        if identity in result:
            fail(f"duplicate catalog identity: {identity}")
        result[identity] = item
    return result


def csv_values(values):
    result = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return list(dict.fromkeys(result))


def write_json(data, output):
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if output:
        pathlib.Path(output).write_text(text, encoding="utf-8")
        print(output)
    else:
        print(text, end="")


def cmd_list(args, catalog):
    items = catalog["components"]
    if args.type:
        items = [item for item in items if item["type"] == args.type]
    for item in items:
        description = item.get("description", "")
        print(f"{item['id']}\t{description}")


def cmd_show(args, catalog):
    item = component_map(catalog).get(args.component)
    if not item:
        fail(f"unknown component: {args.component}")
    write_json(item, None)


def score(item, terms):
    haystack = set(item.get("tags", [])) | set(item.get("capabilities", []))
    return sum(3 if term in item.get("capabilities", []) else 1 for term in terms if term in haystack)


def recommendations(catalog, terms):
    agents = [item for item in catalog["components"] if item["type"] == "agent" and item["name"] != "ceo"]
    skills = [item for item in catalog["components"] if item["type"] == "skill"]
    ranked_agents = sorted(((score(item, terms), item) for item in agents), key=lambda pair: (-pair[0], pair[1]["id"]))
    ranked_skills = sorted(((score(item, terms), item) for item in skills), key=lambda pair: (-pair[0], pair[1]["id"]))
    selected_agents = [item for value, item in ranked_agents if value > 0][:3]
    selected_skills = [item for value, item in ranked_skills if value > 0][:8]
    return selected_agents, selected_skills


def cmd_recommend(args, catalog):
    terms = csv_values(args.tags)
    if not terms:
        fail("provide at least one --tags value")
    agents, skills = recommendations(catalog, terms)
    write_json({
        "goal_tags": terms,
        "agents": [{"id": item["id"], "access": item["access"], "capabilities": item["capabilities"]} for item in agents],
        "advisory_skills": [item["id"] for item in skills],
        "note": "Subagents make the final skill selection within task scope and permissions."
    }, args.output)


def cmd_plan(args, catalog):
    terms = csv_values(args.tags)
    agents, matched_skills = recommendations(catalog, terms)
    matched_ids = [item["id"] for item in matched_skills]
    tasks = []
    for index, agent in enumerate(agents, start=1):
        recommended = list(dict.fromkeys(agent.get("recommended_skills", []) + matched_ids))[:8]
        tasks.append({
            "task_id": f"task-{index:03d}",
            "assigned_agent": agent["id"],
            "objective": f"Contribute {agent['description'].rstrip('.').lower()} to: {args.goal}",
            "permissions": agent["access"],
            "recommended_skills": recommended,
            "status": "ready"
        })
    write_json({
        "schema_version": 1,
        "goal": args.goal,
        "lead": "agent:ceo",
        "skill_authority": "subagent-self-selects",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tasks": tasks
    }, args.output)


def cmd_task(args, catalog):
    components = component_map(catalog)
    agent_id = args.agent if args.agent.startswith("agent:") else f"agent:{args.agent}"
    agent = components.get(agent_id)
    if not agent or agent.get("type") != "agent":
        fail(f"unknown agent: {agent_id}")
    skills = []
    for value in csv_values(args.recommend_skill):
        skill_id = value if value.startswith("skill:") else f"skill:{value}"
        if skill_id not in components or components[skill_id].get("type") != "skill":
            fail(f"unknown skill: {skill_id}")
        skills.append(skill_id)
    packet = {
        "schema_version": 1,
        "task_id": args.task_id,
        "title": args.title,
        "objective": args.objective,
        "assigned_agent": agent_id,
        "scope": csv_values(args.scope),
        "inputs": csv_values(args.input),
        "authoritative_inputs": csv_values(args.authoritative_input),
        "excluded_context": csv_values(args.exclude),
        "context_budget": args.context_budget,
        "recommended_skills": skills,
        "permissions": args.permissions or agent["access"],
        "constraints": csv_values(args.constraint),
        "dependencies": csv_values(args.dependency),
        "acceptance_criteria": csv_values(args.accept),
        "status": "ready"
    }
    errors = validate_task(packet, components)
    if errors:
        fail("; ".join(errors))
    write_json(packet, args.output)


def packet_shape(data, kind):
    if not isinstance(data, dict):
        return [f"{kind} must be an object"]
    common = {"schema_version", "task_id", "status"}
    task_fields = {"title", "objective", "assigned_agent", "scope", "inputs", "authoritative_inputs",
                   "excluded_context", "context_budget", "recommended_skills", "permissions",
                   "constraints", "dependencies", "acceptance_criteria"}
    result_fields = {"agent", "summary", "artifacts", "skills_considered", "skills_applied",
                     "skill_gaps", "evidence", "risks", "recommended_specialist", "next_action"}
    allowed = common | (task_fields if kind == "task" else result_fields)
    required = common | ({"title", "objective", "assigned_agent", "scope", "permissions", "acceptance_criteria"}
                         if kind == "task" else {"agent", "summary", "skills_considered", "skills_applied", "evidence", "risks"})
    errors = [f"{kind} missing {key}" for key in sorted(required - data.keys())]
    errors += [f"{kind} unexpected field {key}" for key in sorted(data.keys() - allowed)]
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        errors.append("schema_version must be integer 1")
    if not isinstance(data.get("task_id"), str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", data["task_id"]):
        errors.append("invalid task_id")
    statuses = ("ready", "running", "review", "complete", "blocked") if kind == "task" else ("complete", "blocked", "needs_specialist", "failed")
    if data.get("status") not in statuses:
        errors.append("invalid status")
    arrays = {"scope", "inputs", "authoritative_inputs", "excluded_context", "recommended_skills",
              "constraints", "dependencies", "acceptance_criteria", "artifacts", "skills_considered",
              "skills_applied", "skill_gaps", "evidence", "risks"}
    for key, value in data.items():
        if key in arrays:
            if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
                errors.append(f"{key} must be an array of nonempty strings")
            elif key in ("recommended_skills", "skills_considered", "skills_applied") and len(set(value)) != len(value):
                errors.append(f"{key} contains duplicates")
        elif key in allowed - {"schema_version"}:
            if value is None and key in ("recommended_specialist", "next_action"):
                continue
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{key} must be a nonempty string")
    return errors


def validate_task(data, components):
    errors = packet_shape(data, "task")
    if errors:
        return errors
    agent = components.get(data["assigned_agent"], {})
    if agent.get("type") != "agent":
        errors.append("assigned_agent must identify an agent")
    if data["permissions"] not in ("read-only", "workspace-write"):
        errors.append("invalid task permissions")
    ceiling = agent.get("access")
    if ceiling not in ("read-only", "workspace-write"):
        errors.append("agent has no valid access ceiling")
    elif ceiling == "read-only" and data["permissions"] == "workspace-write":
        errors.append("task permissions exceed agent access ceiling")
    for skill in data.get("recommended_skills", []):
        if components.get(skill, {}).get("type") != "skill":
            errors.append(f"unknown skill {skill}")
    for field in ("scope", "acceptance_criteria"):
        if not data[field]:
            errors.append(f"{field} cannot be empty")
    return errors


def validate_result(data, components, expected_task=None):
    errors = packet_shape(data, "result")
    if errors:
        return errors
    if components.get(data["agent"], {}).get("type") != "agent":
        errors.append("result agent must identify an agent")
    considered = set(data["skills_considered"])
    applied = set(data["skills_applied"])
    if not applied.issubset(considered):
        errors.append("skills_applied must be a subset of skills_considered")
    for skill in considered | applied:
        if components.get(skill, {}).get("type") != "skill":
            errors.append(f"unknown skill {skill}")
    if data["status"] == "complete" and not data["evidence"]:
        errors.append("completed result requires evidence")
    if expected_task is not None:
        task_errors = validate_task(expected_task, components)
        if task_errors:
            errors.append("expected task is invalid")
        elif data["task_id"] != expected_task["task_id"] or data["agent"] != expected_task["assigned_agent"]:
            errors.append("result does not match assigned task and agent")
    return errors


def cmd_validate(args, catalog):
    path = pathlib.Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read packet: {exc}")
    components = component_map(catalog)
    expected = None
    if args.kind == "result":
        if not args.task:
            fail("result validation requires --task for assignment binding")
        try:
            expected = json.loads(pathlib.Path(args.task).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"cannot read expected task: {exc}")
    errors = validate_task(data, components) if args.kind == "task" else validate_result(data, components, expected)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"{args.kind.capitalize()} packet valid.")


def parser():
    result = argparse.ArgumentParser(description="Inspect and coordinate the .agents team")
    result.add_argument("--home", required=True, help="Explicit approved ecosystem root")
    sub = result.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list")
    list_parser.add_argument("--type", choices=["agent", "skill", "rule", "model", "orchestration", "tool"])
    list_parser.set_defaults(handler=cmd_list)

    show_parser = sub.add_parser("show")
    show_parser.add_argument("component")
    show_parser.set_defaults(handler=cmd_show)

    recommend_parser = sub.add_parser("recommend")
    recommend_parser.add_argument("--tags", action="append", required=True)
    recommend_parser.add_argument("--output")
    recommend_parser.set_defaults(handler=cmd_recommend)

    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--goal", required=True)
    plan_parser.add_argument("--tags", action="append", required=True)
    plan_parser.add_argument("--output")
    plan_parser.set_defaults(handler=cmd_plan)

    task_parser = sub.add_parser("task")
    task_parser.add_argument("--task-id", required=True)
    task_parser.add_argument("--agent", required=True)
    task_parser.add_argument("--title", required=True)
    task_parser.add_argument("--objective", required=True)
    task_parser.add_argument("--scope", action="append", required=True)
    task_parser.add_argument("--input", action="append")
    task_parser.add_argument("--authoritative-input", action="append")
    task_parser.add_argument("--exclude", action="append")
    task_parser.add_argument("--context-budget", default="focused")
    task_parser.add_argument("--recommend-skill", action="append")
    task_parser.add_argument("--permissions", choices=["read-only", "workspace-write"])
    task_parser.add_argument("--constraint", action="append")
    task_parser.add_argument("--dependency", action="append")
    task_parser.add_argument("--accept", action="append", required=True)
    task_parser.add_argument("--output")
    task_parser.set_defaults(handler=cmd_task)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("kind", choices=["task", "result"])
    validate_parser.add_argument("file")
    validate_parser.add_argument("--task", help="Expected assignment, required for results")
    validate_parser.set_defaults(handler=cmd_validate)

    return result


def main():
    args = parser().parse_args()
    home = pathlib.Path(args.home).expanduser().resolve()
    catalog, _ = load_catalog(home)
    args.handler(args, catalog)


if __name__ == "__main__":
    main()
