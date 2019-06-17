from rebrand import run, version


def main():
    import argparse

    p = argparse.ArgumentParser(description="welcome")
    p.add_argument("oldname")
    p.add_argument("newname")
    p.add_argument("sourcedir")
    p.add_argument('destination', default=None)
    args = p.parse_args()
    run(args.oldname, args.newname, args.sourcedir, args.destination)


if __name__ == "__main__":
    main()
