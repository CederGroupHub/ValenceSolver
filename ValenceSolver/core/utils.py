# -*- coding: utf-8 -*-
import re
from unidecode import unidecode
import collections
from sympy.parsing.sympy_parser import parse_expr
from copy import deepcopy
import pkgutil
from pymatgen.core.periodic_table import Element
from .composition_inhouse import CompositionInHouse

if pkgutil.find_loader('Synthepedia'):
    from Synthepedia.concepts.materials.complex import GeneralComposition

__author__ = 'Tanjin He'
__maintainer__ = 'Tanjin He'
__email__ = 'tanjin_he@berkeley.edu'

# convert a dict into orderedDict
def dictOrdered(unordered_dict):
    return collections.OrderedDict(sorted(unordered_dict.items(), key=lambda x:x[0]))

def is_alloy(composition):
    return all([Element(el).is_metal for el in composition])

# TODO: this seems to be an old function and to be removed
def get_valence_single_composition(composition,
                                   all_metal_oxi_states=False,
                                   all_oxi_states=False,
                                   add_compensator=False,
                                   double_el_amt=False):
    """

    :param composition: can be a plain dict or a plain string that pymatgen can interpret
    :return: oxi_state is a dict
    """
    valence_comp = CompositionInHouse(composition)
    valence_comp, inte_factor = valence_comp.get_integer_formula_and_factor()
    valence_comp = CompositionInHouse(valence_comp)

    oxi_state_2 = valence_comp._oxi_state_guesses_most_possible(
        all_metal_oxi_states=all_metal_oxi_states,
        all_oxi_states=all_oxi_states,
        add_compensator=add_compensator,
        double_el_amt=double_el_amt,
    )

    oxi_state = oxi_state_2

    if len(oxi_state) == 0:
        # print('composition: ', composition)
        # print('before relaxation: ', oxi_state)
        oxi_state_2 = valence_comp._oxi_state_guesses_most_possible(
            all_metal_oxi_states=True,
            all_oxi_states=all_oxi_states,
            add_compensator=True,
        )

        oxi_state_1 = valence_comp.oxi_state_guesses(
            all_metal_oxi_states=True,
            all_oxi_states=all_oxi_states,
            add_compensator=True,
            double_el_amt=double_el_amt,
        )

        if len(oxi_state_1) > 0:
            print('compare guess and guess_most_possible')
            print(oxi_state_1)
            print(oxi_state_1[0] == oxi_state_2[0])

        oxi_state = oxi_state_2

        # print('after relaxation: ', oxi_state)
    if len(oxi_state) == 0 and is_alloy(composition):
        oxi_state = [
            {el: 0.0 for el in composition}
        ]
        # print('possible alloy: ', oxi_state)
    if len(oxi_state) > 0 and 'X' in oxi_state[0] and oxi_state[0]['X'] > 0.3:
        if (oxi_state[0]['X'] == 1.0
            and composition['O'] == 2
            and len(composition) == 2
        ):
            # possibly peroxide
            oxi_state[0]['O'] = -1.0
            del oxi_state[0]['X']
        else:
            # possibly wrong composition
            oxi_state = valence_comp._oxi_state_guesses_most_possible(
                all_metal_oxi_states=True,
                all_oxi_states=all_oxi_states,
                add_compensator=True,
                double_el_amt=True
            )
        # print('after double el amt: ', oxi_state)
        # add exception for O2

    return oxi_state


def get_composition_dict(struct_list, elements_vars = {}):
    """
    struct_list is from 'composition' field 
    e.g. [{'amount': '1.0',
             'elements': {'Fe': '12.0',
                          'O': '24.0',
                          'Sr': '6.0'},
             'formula': 'Sr6(Fe2O4)6'}]
    """
    # goal
    combined_comp = {}
    all_comps = []
    
    # get all compositions from struct_list
    for tmp_struct in struct_list:
        if (set(tmp_struct['elements'].keys()) == {'H', 'O'} 
            and len(struct_list) > 1):
            # not take H2O into account
            continue        
        if tmp_struct.get('amount', '1.0') != '1.0':
            # multiply by coefficient if amount is not 1
            tmp_comp = {}
            for ele, num in tmp_struct['elements'].items():
                tmp_comp[ele] = '(' + num + ')*(' + tmp_struct['amount'] + ')'
            all_comps.append(tmp_comp)
        else:
            all_comps.append(tmp_struct['elements'])

    # combine all composition from struct_list
    for tmp_comp in all_comps:
        for k, v in tmp_comp.items():
            if k not in combined_comp:
                combined_comp[k] = v
            else:
                combined_comp[k] += (' + ' + v)

    # element substitution element k -> v
    for k, v in elements_vars.items():
        if k not in combined_comp:
            continue
        if v not in combined_comp:
            combined_comp[v] = combined_comp[k]
        else:
            combined_comp[v] += (' + ' + combined_comp[k])
        del combined_comp[k]

    return combined_comp


def to_GeneralMat_obj(composition, amounts_vars={}, elements_vars={}):
    """
    composition is either a single dict as following or a list of such dicts.
        e.g.     {'amount': '1.0',
                 'elements': {'Fe': '12.0',
                              'O': '24.0',
                              'Sr': '6.0'},
                    ... }
    """
    #     goal
    mat_obj = None
    fraction_vars = {}
    contain_vars = False

    # put composition in a list if it is a dict
    raw_composition = deepcopy(composition)
    if isinstance(raw_composition, dict):
        raw_composition['amount'] = '1.0'
        raw_composition = [raw_composition]
    
    #     get composition after substituting elements variables (e.g. RE -> La)
    composition = get_composition_dict(
        raw_composition,
        elements_vars = elements_vars
    )

    # get fraction_vars/amounts_vars
    # assign fraction_vars
    symbol_replace_dict = {}
    # get value of each variable
    for k, v in amounts_vars.items():
        # greek symbol is not supported by sympy, convert to alphabetical one            
        new_k = unidecode(k)
        if new_k != k:
            new_k = 'greek_' + new_k
            assert new_k not in amounts_vars
            symbol_replace_dict[k] = new_k

        # get value as a list or a range
        if len(v.get('values', [])) > 0:
            fraction_vars[new_k] = v['values']
        else:
            fraction_vars[new_k] = {} 
            if v.get('min_value', None) != None:
                fraction_vars[new_k]['min'] = v['min_value']
            if v.get('max_value', None) != None:
                fraction_vars[new_k]['max'] = v['max_value']
            if len(fraction_vars[new_k]) == 0:
                fraction_vars[new_k] = {'min': 0.0, 'max': 0.0} 
            elif len(fraction_vars[new_k]) == 1:
                fraction_vars[new_k] = list(fraction_vars[new_k].values()) 

    # greek symbol is not supported by sympy, convert to alphabetical one
    for k, new_k in symbol_replace_dict.items():
        for tmp_ele in composition:
            if k in composition[tmp_ele]:
                composition[tmp_ele] = composition[tmp_ele].replace(k, new_k)      
                    
    # deal with extra variables 
    # might from 'amount' in 'composition' field, 
    # which is not in 'amounts_vars'
    # might from del_O
    all_vars = set()
    for ele in composition:
        try:
            tmp_expr = parse_expr(composition[ele])
            all_vars.update(set([str(x) for x in tmp_expr.free_symbols]))
        except:
            pass
    extra_vars = all_vars - set(amounts_vars.keys())
    
    for x in extra_vars:
        # guess del_O as 0.0
        if re.match('del.*', x):
            fraction_vars[x] = [0.0] 
        # assume the amounts are represented by x, y, z (true for most cases)
        # undecared variables other than x, y, z are not considered. 
        # because they might be amount, but also possible to be errors from the text 
        if x in {'x', 'y', 'z'}:
            fraction_vars[x] = [0.0]                    
                    
    if len(fraction_vars):
        contain_vars = True
        
    # get GeneralComposition object
    try:
        mat_obj = GeneralComposition(
            composition=composition, 
            contain_vars=contain_vars, 
            fraction_vars=fraction_vars, 
            edge_composition=[]
        )
    except Exception as e:
        pass

    # check mat_obj is correctly generated
    # because some value of variables might be improper
    try:
        # some value of variables is incredibly large and make the number of element to be negative
        # set skip_wrong_composition = True to skip those wrong values
        # for more strict critera, set skip_wrong_composition = False to skip the entire material
        edge_points = mat_obj.get_critical_compositions(
            skip_wrong_composition=True
        )
        mat_obj.overlap_with(mat_obj)
    except:
        mat_obj = None
    return mat_obj

def merge_valence_as_one(valence_combos):
    valence_all_ele = {}
    could_merge = True
    for combo in valence_combos:
        for ele in combo['valence']:
            if ele not in valence_all_ele:
                valence_all_ele[ele] = []
            valence_all_ele[ele].append(combo['valence'][ele])
    for ele in valence_all_ele:
        if len(set(valence_all_ele[ele])) == 1:
            valence_all_ele[ele] = valence_all_ele[ele][0]
        else:
            could_merge = False
            break
    if not len(valence_all_ele):
        could_merge = False
    if not could_merge:
        valence_all_ele = None
    return could_merge, valence_all_ele

def merge_same_valence(valence_combos):
    valence_dict = {}
    merged_valence = []
    for combo in valence_combos:
        valence_key = str(dictOrdered(combo['valence']))
        if valence_key not in valence_dict:
            valence_dict[valence_key] = []
        valence_dict[valence_key].append(combo)
    for k, v in valence_dict.items():
        merged_valence.append({
            'valence': v[0]['valence'],
            'amounts_vars': [],
            'elements': [],
        })
        for combo in v:
            merged_valence[-1]['amounts_vars'].append(combo['amounts_vars'])
            merged_valence[-1]['elements'].append(combo['elements'])
    return merged_valence

def merge_valence(valence_combos):
    could_merge, valence_all_ele = merge_valence_as_one(valence_combos)
    if could_merge:
        return [{
            'valence': valence_all_ele, 
            'amounts_vars': [combo['amounts_vars'] for combo in valence_combos],
            'elements': [combo['elements'] for combo in valence_combos],
        }]
    else:
        return merge_same_valence(valence_combos)
        
        
def get_material_valence(material, valence_cache={}):
    target_valence = None
    if material:
        # some value of variables is incredibly large and make the number of element to be negative
        # set skip_wrong_composition = True to skip those wrong values
        # for more strict critera, set skip_wrong_composition = False to skip the entire material
        all_comps, var_mapping = material.get_critical_compositions(
            skip_wrong_composition=True,
            return_variable_mapping=True
        )
    else:
        all_comps = []
        var_mapping = []
    all_valence = []
    valence_state_counter = collections.Counter()
    for i, tmp_comp in enumerate(all_comps):
        if not tmp_comp:
            continue
        mat_RCFormula = str(dictOrdered(tmp_comp.composition))
        oxi_state = None
        if mat_RCFormula in valence_cache:
            oxi_state = valence_cache[mat_RCFormula]
        else:
            try:
                oxi_state, _, _ = CompositionInHouse.get_most_possible_oxi_state_of_composition(tmp_comp.composition)
            except:
                oxi_state = None
            if oxi_state and oxi_state[0]:
                oxi_state = oxi_state[0]
                # store in cache:
                valence_cache[mat_RCFormula] = oxi_state
            else:
                oxi_state = None
        if oxi_state:
            all_valence.append({
                'valence': oxi_state,
                'amounts_vars': var_mapping[i],
                'elements': tmp_comp.composition,
            })
            
    all_valence = merge_valence(all_valence)
    if len(all_valence) == 0:
        all_valence = None

    return all_valence
    

