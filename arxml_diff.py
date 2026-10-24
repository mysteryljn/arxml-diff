#!/usr/bin/env python3
import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def local_name(tag): return tag.rsplit("}",1)[-1]
def node_key(node):
    short=next((value for key,value in node.attrib.items() if local_name(key)=="SHORT-NAME"),None)
    return f"{local_name(node.tag)}[{short}]" if short else local_name(node.tag)
def flatten(root):
    output={}
    def visit(node,path):
        output[path]={"tag":local_name(node.tag),"attrs":{local_name(k):v for k,v in sorted(node.attrib.items())},"text":(node.text or "").strip()}
        for index,child in enumerate(list(node)): visit(child,f"{path}/{node_key(child)}[{index}]")
    visit(root,node_key(root)); return output
def diff_files(before,after):
    left,right=flatten(ET.parse(before).getroot()),flatten(ET.parse(after).getroot())
    added=sorted(set(right)-set(left)); removed=sorted(set(left)-set(right)); changed=sorted(path for path in set(left)&set(right) if left[path]!=right[path])
    return {"added":added,"removed":removed,"changed":changed,"ok":not(added or removed or changed)}
def main(argv=None):
    parser=argparse.ArgumentParser(description="Compare two ARXML files structurally"); parser.add_argument("before",type=Path); parser.add_argument("after",type=Path); args=parser.parse_args(argv)
    try: print(json.dumps(diff_files(args.before,args.after),indent=2,ensure_ascii=False))
    except (OSError,ET.ParseError) as exc: print(f"error: {exc}"); return 2
    return 0
if __name__=="__main__": raise SystemExit(main())
