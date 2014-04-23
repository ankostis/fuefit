#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2013-2014 ankostis@gmail.com
#
# This file is part of fuefit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
'''Check cmdline parsing and model building.

Created on Apr 23, 2014

@author: ankostis
'''
import unittest
import networkx as nx

from fuefit.pdcalc import build_func_dependencies_graph, harvest_func, harvest_funcs_factory, filter_common_prefixes, gen_all_prefix_pairs

def def_calculations(params, engine, df):
    from math import pi

    def f1(): engine['fuel_lhv'] = params['fuel'][engine['fuel']]['lhv']
    def f2(): df['rpm']     = df.rpm_norm * (engine.rpm_rated - engine.rpm_idle) + engine.rpm_idle
    def f3(): df['p']       = df.p_norm * engine.p_max
    def f4(): df['fc']      = df.fc_norm * engine.p_max
    def f5(): df['rps']     = df.rpm / 60
    def f6(): df['torque']  = (df.p * 1000) / (df.rps * 2 * pi)
    def f7(): df['pme']     = (df.torque * 10e-5 * 4 * pi) / (engine.capacity * 10e-3)
    def f8(): df['pmf']     = ((4 * pi * engine.fuel_lhv) / (engine.capacity * 10e-3)) * (df.fc / (3600 * df.rps * 2 * pi)) * 10e-5
    def f9(): df['cm']      = df.rps * 2 * engine.stroke / 1000

    return (f1, f2, f3, f4, f5, f6, f7, f8, f9)


class Test(unittest.TestCase):

    def test_filter_common_prefixes(self):
        filter_common_prefixes
        deps = ['a', 'a.b', 'b.cc', 'a.d', 'b', 'ac', 'a.c']
        res = filter_common_prefixes(deps)
        self.assertEqual(res, ['a.b', 'a.c', 'a.d', 'ac', 'b.cc'])

        deps = ['R.df.hh.tt', 'R.df.hh.ll', 'R.df.hh']
        res = filter_common_prefixes(deps) 
        self.assertEqual(res, ['R.df.hh.ll', 'R.df.hh.tt'])
        
    def test_gen_all_prefix_pairs(self):
        path = 'R.foo.com'
        res = gen_all_prefix_pairs(path)
        self.assertEqual(list(res), [('R.foo', 'R'), ('R.foo.com', 'R.foo')])



    def test_harvest_lambda(self):
        func = lambda df: df.hh['tt']

        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.tt', [], func), deps)

    def test_harvest_lambda_successors(self):
        func = lambda df: df.hh['tt'].ss
        deps = harvest_func(func)
        self.assertEqual(deps, [('R.df.hh.tt.ss', [], func)], deps)

        func = lambda df: df.hh['tt'].ss('some_arg')
        deps = harvest_func(func)
        self.assertEqual(deps, [('R.df.hh.tt.ss', [], func)], deps)

        func = lambda df: df.hh['tt'].ss['oo']
        deps = harvest_func(func)
        self.assertEqual(deps, [('R.df.hh.tt.ss.oo', [], func)], deps)

    def test_harvest_lambda_indirectIndex(self):
        func = lambda df, params: df(params.hh['tt'])
        deps = harvest_func(func); print(deps)
        self.assertEqual(deps[0], ('R.df', [], func), deps)
        self.assertEqual(deps[1], ('R.params.hh.tt', [], func), deps)

    def test_harvest_lambda_multiIndex(self):
        func = lambda df, params: df.hh[['tt','ll']] + params.tt
        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.ll', [], func), deps)
        items = [item for (item, _, _) in deps]
        self.assertEqual(items, ['R.df.hh.ll', 'R.df.hh.tt', 'R.params.tt'], deps)

    def test_harvest_lambda_sliceIndex(self):
        func = lambda df, params: df.hh['tt':'ll', 'ii']
        deps = harvest_func(func)
        self.assertEqual(deps[0], ('R.df.hh.ii', [], func), deps)
        self.assertEqual(deps[1], ('R.df.hh.ll', [], func), deps)
        self.assertEqual(deps[2], ('R.df.hh.tt', [], func), deps)
        self.assertEqual(len(deps), 3, deps)

        func = lambda df, params: df.hh[['tt','ll', 'i', params.b]]['g'] + params.tt

    def test_harvest_funcs_factory(self):
        def func_fact(df, params):
            def f0(): df.hh['tt'].kk['ll']  = params.OO['PP'].aa
            def f1(): df.hh[['tt','ll', 'i']]    = params.tt
            def f2(): df.hh['tt':'ll', 'i']    = params.tt
            def f3(): df.hh['tt']

            return (f0, f1, f2, f3)

        deps = harvest_funcs_factory(func_fact)
#         self.assertEqual(deps[0][0], 'R.df.hh.tt.kk.ll', deps)
#         self.assertEqual(deps[0][1], 'R.params.OO.PP.aa', deps)

        self.assertEqual(deps[1][0], 'R.df.hh.tt', deps)
        self.assertEqual(deps[2][0], 'R.df.hh.ll', deps)
        self.assertEqual(deps[3][0], 'R.df.hh.i', deps)
        self.assertEqual(deps[1][1], ['R.params.tt'], deps)

        self.assertEqual(deps[4][0], 'R.df.hh.tt', deps)
        self.assertEqual(deps[5][0], 'R.df.hh.ll', deps)
        self.assertEqual(deps[6][0], 'R.df.hh.i', deps)

        self.assertEqual(deps[7][0], 'R.df.hh.tt', deps)


    def testGatherDeps_smoke(self):
        deps = harvest_funcs_factory(def_calculations)
        print('\n'.join([str(s) for s in deps]))


    def testGatherDepsAndBuldGraph_smoke(self):
        deps = harvest_funcs_factory(def_calculations)
        print('\n'.join([str(s) for s in deps]))

        g = build_func_dependencies_graph(deps)
        print(g.edge)
        print(nx.topological_sort(g))
    #     print(nx.topological_sort_recursive(g))
        for line in sorted(nx.generate_edgelist(g)):
            print(line)




if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()