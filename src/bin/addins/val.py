#!/usr/bin/env python
"""Adds custom validation module to the API project.

This also adds two new validation rules
- unique_to_parent
    - the field must be unique amongst other resources with the same parent_ref, but can
      be repeated within other parents
- unique_ignorecase
    - prevents the same value being considered unique when the only difference is case
      e.g. 'station #1' will be considered the same as 'Station #1', the rule will
      prevent whichever is second from being inserted.

Usage:
    add_val [-h|--help]
      NOTE: Must be run in the project folder

Examples:
    add_val

License:
    MIT License

    Copyright (c) 2021 Michael Ottoson

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
"""

import os
import argparse
import itertools
from libcst import *
import importlib
import eve_utils


class EveServiceInserter(CSTTransformer):
    def __init__(self):
        pass

    def leave_Module(self, original_node, updated_node):
        addition = SimpleStatementLine(
            body=[
                ImportFrom(
                    module=Attribute(
                        value=Name(
                            value='validation',
                            lpar=[],
                            rpar=[],
                        ),
                        attr=Name(
                            value='validator',
                            lpar=[],
                            rpar=[],
                        ),
                        dot=Dot(
                            whitespace_before=SimpleWhitespace(
                                value='',
                            ),
                            whitespace_after=SimpleWhitespace(
                                value='',
                            ),
                        ),
                        lpar=[],
                        rpar=[],
                    ),
                    names=[
                        ImportAlias(
                            name=Name(
                                value='EveValidator',
                                lpar=[],
                                rpar=[],
                            ),
                            asname=None,
                            comma=MaybeSentinel.DEFAULT,
                        ),
                    ],
                    relative=[],
                    lpar=None,
                    rpar=None,
                    semicolon=MaybeSentinel.DEFAULT,
                    whitespace_after_from=SimpleWhitespace(
                        value=' ',
                    ),
                    whitespace_before_import=SimpleWhitespace(
                        value=' ',
                    ),
                    whitespace_after_import=SimpleWhitespace(
                        value=' ',
                    ),
                ),
            ])

        new_body = eve_utils.insert_import(updated_node.body, addition)

        return updated_node.with_changes(
            body = new_body
        )

    def visit_SimpleStatementLine(self, node):
        if not isinstance(node.body[0], Assign):
            return False
            
        target = node.body[0].targets[0].target
        
        if not isinstance(target, Attribute):
            return False
            
        if not (target.value.value == 'self' and target.attr.value == '_app'):
            return False
            
        return True
        
    def leave_Assign(self, original_node, updated_node):
        addition = Arg(
            value=Name(
                value='EveValidator',
                lpar=[],
                rpar=[],
            ),
            keyword=Name(
                value='validator',
                lpar=[],
                rpar=[],
            ),
            equal=AssignEqual(
                whitespace_before=SimpleWhitespace(
                    value='',
                ),
                whitespace_after=SimpleWhitespace(
                    value='',
                ),
            ),
            comma=MaybeSentinel.DEFAULT,
            star='',
            whitespace_after_star=SimpleWhitespace(
                value='',
            ),
            whitespace_after_arg=SimpleWhitespace(
                value='',
            ),
        )
        
        comma = Comma(
            whitespace_before=SimpleWhitespace(
                value='',
            ),
            whitespace_after=SimpleWhitespace(
                value=' ',
            ),
        )       

        new_args = []
        last_arg = updated_node.value.args[-1].with_changes(comma=comma)

        for item in itertools.chain(updated_node.value.args[0:-1], [last_arg, addition]):
            new_args.append(item)

        new_value = updated_node.value.with_changes(args=new_args)

        return updated_node.with_changes(
            value = new_value
        )


def wire_up_service():
    with open('eve_service.py', 'r') as source:
        tree = parse_module(source.read())
    
    inserter = EveServiceInserter()
    new_tree = tree.visit(inserter)
    
    with open('eve_service.py', 'w') as source:
        source.write(new_tree.code)
        
        
def add_validation():        
    project_name = os.path.basename(os.getcwd())
    eve_utils.copy_skel(project_name, 'validation')
    eve_utils.install_packages(['isodate'], 'add_val')
    wire_up_service()


def main():
    parser = argparse.ArgumentParser('add_val', description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    args = parser.parse_args()

    if not os.path.exists('./requirements.txt'):
        print('requirements.txt missing - must be run in the API folder')
        quit(1)
        
    if not os.path.exists('./domain'):
        print('domain folder missing - must be run in the API folder')
        quit(2)
        
    if os.path.exists('./validation'):
        print('validation folder already exists')
        quit(3)
        
    add_validation()

    print('validation module added')


if __name__ == '__main__':
    main()