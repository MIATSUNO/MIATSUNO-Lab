# secure_passphrase

A local password and passphrase generator that uses Python's `secrets` module. It never saves, uploads, or prints anything except the newly generated values.

## Installation

Requires Python 3.9 or newer. No third-party packages are needed.

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 secure_passphrase.py --help
```

## Usage

The exact command help is:

```text
usage: secure_passphrase.py [-h] [--mode {password,passphrase}] [--length LENGTH]
                            [--words WORDS] [--separator SEPARATOR]
                            [--no-symbols] [--capitalize] [--digits]
                            [--count COUNT]

Generate secrets locally with Python's cryptographically secure random source.

options:
  -h, --help            show this help message and exit
  --mode {password,passphrase}
                        generate characters or words (default: passphrase)
  --length LENGTH       password character count (default: 24)
  --words WORDS         passphrase word count (default: 5)
  --separator SEPARATOR
                        passphrase separator (default: -)
  --no-symbols          omit punctuation in password mode
  --capitalize          capitalize each passphrase word
  --digits              append four random digits to a passphrase
  --count COUNT         number of independent secrets to print (default: 1)
```

## Examples

```bash
python3 secure_passphrase.py
python3 secure_passphrase.py --mode password --length 32 --count 3
python3 secure_passphrase.py --mode passphrase --words 6 --capitalize --digits
```

## Audience

People creating account credentials locally, students studying secure random generation, and operators who need a quick terminal secret generator.

## Limitations

The built-in word list is intentionally small, so passphrases are less flexible than a mature password manager's generator. The tool cannot store or autofill credentials. Do not use generated output for a high-value account without considering a dedicated password manager and its recovery plan.

## Safety notes

The output is sensitive as soon as it is generated. Avoid shell history, screenshots, shared terminals, and logs. The program does not guarantee clipboard clearing or secure memory erasure; transfer values directly to a password manager and rotate any value that may have been exposed.
