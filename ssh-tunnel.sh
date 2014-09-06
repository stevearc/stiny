#!/bin/bash

main() {
    while true; do
        ssh -nNTy -i /home/pi/.ssh/id_rsa -R 9000:localhost:6543 pi@home.stevearc.com
        sleep 300
    done
}

main "$@"
