import os
from colorama import Fore
from collections import defaultdict
import os
import string
import re
import shutil
from pathlib import Path
from pprint import pprint
from textsearch import TextSearch

BOUNDS = set(string.digits + string.ascii_letters)

BLOCKED = set(["node_modules", ".git", "__pycache__"])


def handle_file(r, file_path, data):
    new_path = r.replace(file_path)
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
    new_txt = r.replace(txt)
    if txt != new_txt:
        data["files_content_change"].append(new_path)
        with open(new_path, "w", encoding="utf8") as f:
            f.write(new_txt)


def recurse_path(top, r, data=None):
    if data is None:
        data = defaultdict(list)
    if os.path.isdir(top):
        data["directories_visited"].append(top)
        new_path = r.replace(top)
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
            recurse_path(child_path, r, data)
        return data, top
    elif os.path.isfile(top):
        data["files_visited"].append(top)
        handle_file(r, top, data)
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
joiners = ["", "\-", "_", " ", "__", "\."]
special_case = [pascalcase, camelcase]


def ts_replacer(a, b):
    # lowercase letters before are allowed, how about a second one...
    # ts = TextSearch("sensitive", "norm", ALPHANUM - ALPHA_LOWER, ALPHANUM)
    ts = TextSearch("sensitive", "norm", BOUNDS, BOUNDS)

    found_sep_in_b = ""
    for x in [" ", "-", "_", "."]:
        if x in b:
            found_sep_in_b = x
            break

    # a = ["some", "thing"]
    # b = ["another", "thing"]

    aa = normalize(a)
    bb = normalize(b)

    # questions like:
    # - prefer camelCase for word2 when word1 is lowercase
    # - prefer Halftitle, PascalCase/Titlecase for word2 when word1 is titlecase
    # etc
    # below... lower order means higher prio
    for s in [".", "_", "-", found_sep_in_b, ""]:
        # halftitle
        x = aa[0][0].title() + s.join(aa)[1:]
        y = bb[0][0].title() + s.join(bb)[1:]
        ts.add(x, y)

        # camelCase
        x = s.join([aa[0].lower()] + [x.title() for x in aa[1:]])
        y = s.join([bb[0].lower()] + [x.title() for x in bb[1:]])
        ts.add(x, y)

        # easy cases
        for c in [str.upper, str.title, str.lower]:
            x = s.join([c(x) for x in aa])
            y = s.join([c(x) for x in bb])
            ts.add(x, y)

    # ts.add("SomeThing", "AnotherThing")
    ts.add(a, b)

    return ts


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


def run(old_name, new_name, toplevel_path, destination=None, escape=True, verbose=False):
    ts = ts_replacer(old_name, new_name)
    toplevel_path = os.path.abspath(toplevel_path)
    if not os.path.isdir(toplevel_path):
        raise ValueError("Should give a valid path to search")
    if destination is None:
        destination = ts.replace(toplevel_path)
    if os.path.exists(destination):
        raise ValueError("Destination '{}' already exists".format(destination))
    # when taking the gloves off
    # if os.path.isdir(backup_path):
    #    shutil.rmtree(backup_path)
    shutil.copytree(toplevel_path, destination)
    data, new_top = recurse_path(destination, ts)
    data = dict(data)
    print_results(data, new_top)
