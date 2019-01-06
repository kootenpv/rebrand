from colorama import Fore
from collections import defaultdict
import os
import string
import re
import shutil
from pathlib import Path
from pprint import pprint

LOWERCASE = set(string.ascii_lowercase)
UPPERCASE = set(string.ascii_uppercase)

BLOCKED = set(["node_modules", ".git", "__pycache__"])


def handle_file(scanner, file_path, data):
    new_path = replace(scanner, file_path)
    if file_path != new_path:
        data["files_moved"].append((file_path, new_path))
    try:
        with open(file_path, "r", encoding="utf8") as f:
            txt = f.read()
        if file_path != new_path:
            os.remove(file_path)
    except UnicodeDecodeError:
        data["binary_files_moved"].append((file_path, new_path))
        # print("[E] Unable to do anything with binary file", new_path)
        shutil.move(file_path, new_path)
        return
    new_txt = replace(scanner, txt)
    if txt != new_txt:
        data["files_content_change"].append(new_path)
        with open(new_path, "w", encoding="utf8") as f:
            f.write(new_txt)


def recurse_path(top, scanner, data=None):
    if data is None:
        data = defaultdict(list)
    if os.path.isdir(top):
        data["directories_visited"].append(top)
        new_path = replace(scanner, top)
        if top != new_path:
            data["directories_moved"].append((top, new_path))
            shutil.move(top, new_path)
            top = new_path
        try:
            children = os.listdir(top)
        except PermissionError:
            data["permission_error"].append(top)
            return data
        for child_name in children:
            child_path = os.path.join(top, child_name)
            if child_name in BLOCKED:
                # shutil.move(top, new_path)
                continue
            recurse_path(child_path, scanner, data)
        return data, top
    elif os.path.isfile(top):
        data["files_visited"].append(top)
        handle_file(scanner, top, data)
    else:
        print("ERR", top)
    return data, top


def camelcase(tokens, sep):
    if sep != "":
        raise ValueError("just for safety, sep has to be empty")
    # camelCase
    tokens = [tokens[0].lower()] + [x.title() for x in tokens[1:]]
    return "".join(tokens)


def pascalcase(tokens, sep):
    if sep != "":
        raise ValueError("just for safety, sep has to be empty")
    # "PascalCase
    return "".join([x.title() for x in tokens])


def lowercase(tokens, sep):
    return sep.join(tokens).lower()


def uppercase(tokens, sep):
    return sep.join(tokens).upper()


def titlecase(tokens, sep):
    # Titlecase
    if len(tokens) == 1:
        return tokens[0].title()
    return " ".join(tokens).title().replace(" ", sep)


def halftitlecase(tokens, sep):
    # Titlecase
    return tokens[0].title() + sep + lowercase(tokens[1:], sep)


def normalize(name):
    for join in joiners[1:]:
        name = name.replace(join, "_")
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return [x.strip() for x in re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower().split("_") if x]


casing = [uppercase, titlecase, halftitlecase, lowercase]
joiners = ["", "-", "_", " ", "__", "\."]
special_case = [pascalcase, camelcase]


class Rule:
    def __init__(self, pre, x, y, post, case, sep, esc, verbose):
        self.verbose = verbose
        self.esc = esc
        self.pre = pre
        self.post = post
        self.y = y
        self.case = case
        self.sep = sep
        self.verbose = verbose
        self.escape = re.escape if esc else lambda x: x
        fn = self.transform if verbose else self.constant()
        self.scan_tuple = (self.regex(x), fn)

    def constant(self):
        return self.transform("", "")

    def regex(self, x):
        regex = self.pre + self.escape(self.case(x, self.sep)) + self.post
        return regex

    @property
    def name(self):
        return self.pre + "|" + self.case.__name__ + "|" + self.post + "|" + self.sep

    def __repr__(self):
        return "Rule: " + self.name

    def transform(self, scanner, x):
        # scanner and x unused indeed
        if self.verbose:
            print(self.name)
        if self.pre == "\\.":
            pre = "."
        elif self.pre in joiners:
            pre = self.pre
        else:
            pre = ""
        if self.post == "\.":
            post = "."
        elif self.post in joiners:
            post = self.post
        else:
            post = ""
        if self.sep == "\.":
            sep = "."
        elif self.sep in joiners:
            sep = self.sep
        else:
            sep = ""
        return pre + self.escape(self.case(self.y, sep)) + post


def get_scanner(a, b, escape, verbose):
    X = normalize(a)
    Y = normalize(b)
    rules = []

    # letters before are okay, after not
    r = Rule("(?<![^a-zA-Z0-9 ])", X, Y, "(?![a-z])", pascalcase, "", escape, verbose)
    rules.append(r)
    # letters before are not okay, after okay
    r = Rule("(?<![a-z])", X, Y, "(?<![^a-zA-Z0-9 ])", camelcase, "", escape, verbose)
    rules.append(r)

    # first pre, then post, then neither
    for pre_, post_ in [(True, False), (False, True), (False, False)]:
        for case in casing:
            for sep in joiners:
                pre = sep if pre_ else "\\b"
                post = sep if post_ else "\\b"

                rule = Rule(pre, X, Y, post, case, sep, escape, verbose)
                rules.append(rule)

    # return rules
    scans = [x.scan_tuple for x in rules]
    scans.append((".", lambda scanner, x: x))
    scanner = re.Scanner(scans, flags=re.DOTALL)
    return scanner


def replace(scanner, c):
    match, _ = scanner.scan(c)
    return "".join(match)


def colorize(old, new):
    olds = old.split("/")
    news = new.split("/")
    o = []
    n = []
    for a, b in zip(olds, news):
        if a != b:
            a = Fore.RED + a + Fore.RESET
            b = Fore.GREEN + b + Fore.RESET
        o.append(a)
        n.append(b)
    return "{} -> {}".format("/".join(o), "/".join(n))


def print_results(data, new_top):
    any_change = False
    for x in ['directories_moved', 'files_moved', 'binary_files_moved', "files_content_change"]:
        if x in data:
            any_change = True
            print(Fore.YELLOW + x.upper() + Fore.RESET)
            if "moved" in x:
                for old, new in data[x]:
                    print(colorize(old, new))
                print()
            else:
                for changed_file in data[x]:
                    print(changed_file)
                print()
    if not any_change:
        for x in ["directories_visited", "files_visited"]:
            print(Fore.YELLOW + x.upper() + Fore.RESET, len(data[x]))
        print()
    for x in ["permission_error"]:
        if x in data:
            print(Fore.YELLOW + x.upper() + Fore.RESET)
            for y in data[x]:
                print(y)
            print()
    image_warning_printed = False
    for tag in ["logo", "icon"]:
        for suffix in ["png", "jpg"]:
            for x in Path(new_top).glob(f"**/*{tag}*.{suffix}"):
                if not image_warning_printed:
                    print(Fore.YELLOW + "IMAGES_REQUIRING_ATTENTION" + Fore.RESET)
                    image_warning_printed = True
                print(x)


def run(old_name, new_name, toplevel_path, escape=True, verbose=False):
    # 0. backup
    if not os.path.isdir(toplevel_path):
        raise ValueError("should give a path")
    toplevel_path = os.path.abspath(toplevel_path)
    backup_path = toplevel_path + "_rebranded"
    if os.path.isdir(backup_path):
        shutil.rmtree(backup_path)
    shutil.copytree(toplevel_path, backup_path)
    # 1. replacement
    scanner = get_scanner(old_name, new_name, escape=escape, verbose=verbose)
    data, new_top = recurse_path(backup_path, scanner)
    data = dict(data)
    print_results(data, new_top)
