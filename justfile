version := `uv version | awk '{print $2}'`
sqlc_version := `uv version | awk '{print $2}' | sed 's/\.post.*//'`
sqlc_src := "/tmp/sqlc-build"

clone:
    rm -rf {{sqlc_src}}
    git clone --depth 1 --branch v{{sqlc_version}} https://github.com/sqlc-dev/sqlc.git {{sqlc_src}}
    cp {{sqlc_src}}/cmd/sqlc/main.go {{sqlc_src}}/main.go
    rm {{sqlc_src}}/placeholder.go

local_platform := `uname -s | tr A-Z a-z` + "-" + `uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/'`

build-local: clone
    rm -rf dist
    CGO_ENABLED=1 uv run python build_wheel.py {{sqlc_src}} \
        --name sqlc --version {{version}} --entry-point sqlc \
        --platform {{local_platform}}
    rm -rf {{sqlc_src}}

release version:
    uv version {{ version }}
    git add --all
    git commit --message "Release v{{ version }}"
    git push
    git tag --annotate v{{ version }} --message v{{ version }}
    git push --tags
