# Supported target: Linux arm64 / CPython 3.12. No build arguments or secrets.
FROM python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS fetch
WORKDIR /fetch
COPY requirements.lock /fetch/requirements.lock
RUN python -I -c "import platform,sys; assert platform.machine() == 'aarch64' and sys.version_info[:2] == (3,12), 'Linux arm64 / Python 3.12 required'"
RUN python -I -m pip --isolated download --disable-pip-version-check --no-cache-dir --require-hashes --only-binary=:all: --no-deps --index-url https://pypi.org/simple --timeout 10 --retries 0 --dest /fetch/wheels -r /fetch/requirements.lock
ADD --checksum=sha256:ea6f4e5d40d9ba0d73a801515772962f1c7cc8ab8932a4de41a573b46411070d https://codeload.github.com/NVIDIA/SkillSpector/tar.gz/c7958a3268d9498644b22edb75d0f051bbc8cbfc /fetch/source.tar.gz

FROM python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS build
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
COPY --from=fetch /fetch /fetch
COPY requirements.lock extract_source.py build_wheel.py /build/
RUN --network=none mkdir /engine && chown -R 65534:65534 /build /engine && chmod 644 /fetch/source.tar.gz
USER 65534:65534
RUN --network=none python -I -B /build/extract_source.py /fetch/source.tar.gz /build/source
RUN --network=none python -I -m pip --isolated install --disable-pip-version-check --no-cache-dir --no-compile --require-hashes --only-binary=:all: --no-deps --no-index --find-links /fetch/wheels --target /engine/site -r /build/requirements.lock
RUN --network=none python -I -B /build/build_wheel.py
RUN --network=none python -I -m pip --isolated install --disable-pip-version-check --no-cache-dir --no-compile --no-deps --no-index --target /engine/site /build/wheels/skillspector-2.12.0-py3-none-any.whl
ENV PYTHONPATH=/engine/site
RUN --network=none python -m pip --isolated check && python -c "from importlib.metadata import version; assert version('skillspector') == '2.12.0'"

FROM python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS runtime
COPY --from=build /engine/site /engine/site
COPY --from=build /engine/provenance.json /engine/provenance.json
ENV PYTHONPATH=/engine/site PYTHONDONTWRITEBYTECODE=1
USER 65534:65534
WORKDIR /tmp
CMD ["python", "-c", "from importlib.metadata import version; print('SkillSpector ' + version('skillspector'))"]
