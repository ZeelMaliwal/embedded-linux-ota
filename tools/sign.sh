#!/bin/bash
set -euo pipefail

# sign firmware images with ed25519
# requires openssl 3.0+

case "${1:-}" in
    genkey)
        openssl genpkey -algorithm ed25519 -out ota-signing.key
        openssl pkey -in ota-signing.key -pubout -out ota-signing.pub
        echo "keys generated: ota-signing.key (private), ota-signing.pub (public)"
        echo "keep the private key safe, deploy the public key to devices"
        ;;
    sign)
        [[ -z "${2:-}" ]] && echo "usage: $0 sign <file> [keyfile]" && exit 1
        KEYFILE="${3:-ota-signing.key}"
        openssl pkeyutl -sign -inkey "$KEYFILE" -rawin -in "$2" -out "$2.sig"
        echo "signed: $2.sig"
        ;;
    verify)
        [[ -z "${2:-}" ]] && echo "usage: $0 verify <file> [pubkey]" && exit 1
        PUBKEY="${3:-ota-signing.pub}"
        if openssl pkeyutl -verify -pubin -inkey "$PUBKEY" -rawin -in "$2" -sigfile "$2.sig"; then
            echo "signature valid"
        else
            echo "SIGNATURE INVALID"
            exit 1
        fi
        ;;
    *)
        echo "usage: $0 {genkey|sign <file>|verify <file>}"
        ;;
esac
