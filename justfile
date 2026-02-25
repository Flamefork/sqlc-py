version := `uv version | awk '{print $2}'`
sqlc_src := "/tmp/sqlc-build"

clone:
    rm -rf {{sqlc_src}}
    git clone --depth 1 --branch v{{version}} https://github.com/sqlc-dev/sqlc.git {{sqlc_src}}
    cp {{sqlc_src}}/cmd/sqlc/main.go {{sqlc_src}}/main.go
    rm {{sqlc_src}}/placeholder.go

build: clone
    rm -rf dist
    uv run go-to-wheel {{sqlc_src}} \
        --name sqlc \
        --version {{version}} \
        --entry-point sqlc \
        --description "sqlc - Generate type-safe code from SQL" \
        --license MIT \
        --url https://github.com/sqlc-dev/sqlc
    rm -rf {{sqlc_src}}

build-local: clone
    rm -rf dist
    uv run go-to-wheel {{sqlc_src}} \
        --name sqlc \
        --version {{version}} \
        --entry-point sqlc \
        --platforms darwin-arm64 \
        --description "sqlc - Generate type-safe code from SQL" \
        --license MIT \
        --url https://github.com/sqlc-dev/sqlc
    rm -rf {{sqlc_src}}

release version:
    uv version {{ version }}
    git add --all
    git commit --message "Release v{{ version }}"
    git push
    git tag --annotate v{{ version }} --message v{{ version }}
    git push --tags
