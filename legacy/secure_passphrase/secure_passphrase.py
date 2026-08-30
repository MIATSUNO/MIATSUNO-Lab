#!/usr/bin/env python3
import argparse
import secrets
import string

WORDS = """amber anchor apple atlas autumn bamboo beacon berry birch breeze bronze cactus canyon cedar cherry cobalt comet copper coral cosmos cricket crystal dawn delta desert ember fern flame forest frost galaxy garden glacier harbor hazel island jasmine juniper lantern lavender lemon maple marble meadow mercury mist moon mountain nectar ocean olive orchid pebble pepper pine planet plum quartz raven river robin rocket rose saffron sage salmon shadow silver solar sparrow spring spruce star stone storm summit sunset thistle thunder tiger topaz valley violet walnut willow winter wizard yellow zenith""".split()


def secure_password(length, symbols):
    alphabet = string.ascii_letters + string.digits
    if symbols:
        alphabet += "!@#$%^&*()-_=+[]{}:,.?"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def secure_passphrase(word_count, separator, capitalize, digits):
    words = [secrets.choice(WORDS) for _ in range(word_count)]
    if capitalize:
        words = [word.capitalize() for word in words]
    value = separator.join(words)
    if digits:
        value += separator + str(secrets.randbelow(10000)).zfill(4)
    return value


def build_parser():
    parser = argparse.ArgumentParser(description="Generate secrets locally with Python's cryptographically secure random source.")
    parser.add_argument("--mode", choices=("password", "passphrase"), default="passphrase", help="generate characters or words (default: passphrase)")
    parser.add_argument("--length", type=int, default=24, help="password character count (default: 24)")
    parser.add_argument("--words", type=int, default=5, help="passphrase word count (default: 5)")
    parser.add_argument("--separator", default="-", help="passphrase separator (default: -)")
    parser.add_argument("--no-symbols", action="store_true", help="omit punctuation in password mode")
    parser.add_argument("--capitalize", action="store_true", help="capitalize each passphrase word")
    parser.add_argument("--digits", action="store_true", help="append four random digits to a passphrase")
    parser.add_argument("--count", type=int, default=1, help="number of independent secrets to print (default: 1)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.count < 1 or args.count > 100:
        parser.error("--count must be between 1 and 100")
    if args.mode == "password" and not 8 <= args.length <= 512:
        parser.error("--length must be between 8 and 512 in password mode")
    if args.mode == "passphrase" and not 3 <= args.words <= 20:
        parser.error("--words must be between 3 and 20 in passphrase mode")
    for _ in range(args.count):
        if args.mode == "password":
            print(secure_password(args.length, not args.no_symbols))
        else:
            print(secure_passphrase(args.words, args.separator, args.capitalize, args.digits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

