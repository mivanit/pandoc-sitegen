"""python pandoc filter replicating [pandoc-csv2table](https://hackage.haskell.org/package/pandoc-csv2table)

By [@mivanit](mivanit.github.io)
"""


from optparse import Option
from typing import *
import os
import io
import sys
import subprocess
import csv

from pandocfilters import toJSONFilter, Table, Plain, Str


ALIGN_MAP : Dict[str,str] = {
    'L' : 'AlignLeft',
    'C' : 'AlignCenter',
    'R' : 'AlignRight',
    'D' : 'AlignDefault',
}

emptyblock = lambda : ["",[],[]]

def Plain_factory(val : str) -> List:
    return {
        "t" : "Plain",
        "c" : [
            {"t" : "Str", "c" : val.strip()}
            # for w in val.split()
        ],
    }

def table_cell_factory(val : str) -> List:
    return [
        emptyblock(),
        { "t": "AlignDefault" },
        1,
        1,
        [ Plain_factory(val) ],
    ]

def table_row_factory(lst_vals : List) -> List:
    return [
        emptyblock(),
        [
            table_cell_factory(val)
            for val in lst_vals
        ]
    ]

def header_factory(lst_vals : List) -> List:
    return [
        emptyblock(),
        [ table_row_factory(lst_vals) ],
    ]

def body_factory(table_vals : List) -> List:
    return [[
        emptyblock(),
        0,
        [],
        [
            table_row_factory(row)
            for row in table_vals
        ],
    ]]

def keyvals_process(keyvals : List[Tuple[str, str]]) -> Dict[str,str]:
    return {
        key : val
        for key, val in keyvals
    }


    

def codeblock_process(key, value, format_, _):
    # figure out whether this block should be processed
    if not (key == 'CodeBlock'):
        return None
    
    [[ident, classes, lst_keyvals], code] = value

    if "csv_table" not in classes:
        return None

    # read the keyvals
    keyvals : dict = keyvals_process(lst_keyvals)
    header : bool = bool(int(keyvals.get("header", 1)))
    source : Optional[str] = keyvals.get("source")
    aligns : Optional[List[str]] = (
        list(keyvals.get("aligns", "")) 
        if "aligns" in keyvals 
        else None
    )
    caption : Optional[str] = keyvals.get("caption", None)

    # read the csv source into a table
    if source is None:
        table_data = list(csv.reader(io.StringIO(code)))
    else:
        if os.path.isfile(source):
            table_data = list(csv.reader(open(source, "r")))
        else:
            raise Exception(f"csv source file not found: {source}")

    # validate the csv table
    n_cols : int = len(table_data[0])
    assert all(
        len(row) == n_cols 
        for row in table_data
        ), "csv table is not rectangular"
    
    if aligns is None:
        aligns = [ "D" for _ in range(n_cols) ]
    else:
        if len(aligns) == 1:
            aligns = [ aligns[0].upper() for _ in range(n_cols) ]
        elif len(aligns) == n_cols:
            aligns = [ aln.upper() for aln in aligns ]        
        else:
            raise Exception(f"aligns length mismatch: {aligns}")
    
    if header:
        row_header : List = table_data[0]
        table_rows : List = table_data[1:]
    else:
        raise Exception("lack of header not supported")
        row_header = []
        table_rows = table_data
    

    # write the table
    return {
        "t": "Table",
        "c" : [
            # idk
            emptyblock(),
            # caption
            [
                None,
                [] if caption is None else [ Plain_factory(caption) ], 
            ],
            # aligns
            [
                [ 
                    { "t" : ALIGN_MAP[aln] }, 
                    { "t" : "ColWidthDefault" },
                ]
                for aln in aligns
            ],
            # header
            header_factory(row_header),
            # rows
            body_factory(table_rows),
            # ???
            [
                emptyblock(),
                []
            ],
        ]
    }


def test_filter():
    import json
    with open(sys.argv[1]) as f:
        data = json.load(f)
    key = data["blocks"][0]["t"]
    value = data["blocks"][0]["c"]
    newdata = codeblock_process(key, value, "", "")
    print(json.dumps(newdata, indent=2))


if __name__ == "__main__":
    toJSONFilter(codeblock_process)
    # test_filter()
    


