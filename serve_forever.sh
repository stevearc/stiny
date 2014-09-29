#!/bin/bash -e

main() {
    . stiny_env/bin/activate
    go run build.go -w &
    pip install waitress

    while [ 1 ]; do
        pserve --reload development.ini
        sleep 1
    done
}

main "$@"
