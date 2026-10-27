#!/usr/bin/env python3
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def local_name(tag): return tag.rsplit("}",1)[-1]

def namespace_uri(tag):
    """Return an expanded XML tag's namespace URI, if it has one.

    ElementTree represents namespaced names as ``{uri}local``.  Keeping the
    URI separate from the local name lets paths remain stable when a prefix
    changes while still detecting a change to the schema namespace itself.
    """
    if isinstance(tag, str) and tag.startswith("{"):
        end = tag.find("}")
        if end > 1:
            return tag[1:end]
    return None

def expanded_name(tag):
    uri = namespace_uri(tag)
    return f"{{{uri}}}{local_name(tag)}" if uri else local_name(tag)

def _path_key(node):
    """Return a stable child key, disambiguating colliding XML namespaces.

    ARXML commonly uses the same local element name in multiple namespaces.
    Paths historically used only the local name, so ``a:X`` and ``b:X`` were
    assigned the same occurrence sequence.  Inserting one of those elements
    then made unrelated nodes appear changed.  Keep the compact legacy path
    for unqualified elements while always including the namespace URI for a
    qualified element; this makes qualified and unqualified keys distinct
    without relabelling an existing unqualified node when a sibling appears.
    """
    base = node_key(node)
    # Namespace-qualified nodes always carry their namespace in the path so
    # the path remains stable when a sibling from another namespace appears.
    if namespace_uri(node.tag) is not None:
        return f"{base}@{expanded_name(node.tag)}"
    return base
def node_key(node):
    short=next((value for key,value in node.attrib.items() if local_name(key)=="SHORT-NAME"),None)
    if short is None:
        short=next(
            ((child.text or "").strip() for child in list(node) if local_name(child.tag)=="SHORT-NAME"),
            None,
        )
    return f"{local_name(node.tag)}[{short}]" if short else local_name(node.tag)
def flatten(root):
    output, _ = _flatten(root)
    return output

def _flatten(root):
    output={}
    orders={}
    # Walk iteratively so a deeply nested (but valid) ARXML file cannot
    # exhaust Python's recursion limit and crash a diff/CI job.
    pending=[(root,node_key(root))]
    while pending:
        node,path=pending.pop()
        children = list(node)
        output[path]={
            "tag":local_name(node.tag),
            "namespace":namespace_uri(node.tag),
            "attrs":{local_name(k):v for k,v in sorted(node.attrib.items())},
            # Keep the local-name attribute view for compatibility, but also
            # retain expanded names so namespace changes cannot be lost.
            "attr_qnames":{expanded_name(k):v for k,v in sorted(node.attrib.items())},
            "text":(node.text or "").strip(),
            # ElementTree stores text after a child in that child's ``tail``
            # field.  Include it so mixed-content changes (for example, a
            # changed description suffix) are not silently missed.
            "tail":(node.tail or "").strip(),
        }
        occurrences={}
        child_paths=[]
        for child in children:
            key=_path_key(child)
            index=occurrences.get(key,0)
            occurrences[key]=index+1
            child_path=f"{path}/{key}[{index}]"
            child_paths.append(child_path)
        orders[path]=child_paths
        # Preserve document order while using a LIFO stack.
        pending.extend(reversed(list(zip(children, child_paths))))
    return output, orders
def diff_files(before,after):
    left,left_orders=_flatten(ET.parse(before).getroot())
    right,right_orders=_flatten(ET.parse(after).getroot())
    added=sorted(set(right)-set(left)); removed=sorted(set(left)-set(right)); changed=sorted(path for path in set(left)&set(right) if left[path]!=right[path])
    order_changed=[]
    for path in sorted(set(left_orders)&set(right_orders)):
        common=set(left_orders[path])&set(right_orders[path])
        left_order=[child for child in left_orders[path] if child in common]
        right_order=[child for child in right_orders[path] if child in common]
        if left_order != right_order:
            order_changed.append(path)
    return {"added":added,"removed":removed,"changed":changed,"order_changed":order_changed,"ok":not(added or removed or changed or order_changed)}
def main(argv=None):
    parser=argparse.ArgumentParser(description="Compare two ARXML files structurally"); parser.add_argument("before",type=Path); parser.add_argument("after",type=Path); args=parser.parse_args(argv)
    try: print(json.dumps(diff_files(args.before,args.after),indent=2,ensure_ascii=False))
    except (OSError,ET.ParseError) as exc: print(f"error: {exc}"); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
