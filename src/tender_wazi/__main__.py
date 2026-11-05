import os
import sys

from tender_wazi.migrate import migrate


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate(os.environ["DATABASE_URL_DIRECT"])
        return
    print("usage: python -m tender_wazi migrate", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
