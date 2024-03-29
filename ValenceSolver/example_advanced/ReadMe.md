Advanced usage to work with other packages. Not needed in common cases. 

With a dataset file, where there might be variables of elements and amount, the minimal code is as following. We first create a `GeneralComposition` object using `Synthepedia`. `GeneralComposition` is able to generate all composition instances by substituting varibles in formula and to check if the stoichiometric number is valid (should not be negative) after substitution. Then, we solve the valence by calling `get_material_valence(tmp_mat_obj, valence_cache=valence_cache)`. The valence_cache is optional, which is designed to save solved cases to avoid duplication in the future. It can be initialized as an emtpy dict and the value would be updated automatically after calling `get_material_valence`. (example in example/example_for_reactions.py)

    from ValenceSolver.core.utils import to_GeneralMat_obj, get_material_valence
    
    tmp_mat_obj = to_GeneralMat_obj(
        composition=composition,
        amounts_vars=amounts_vars,
        elements_vars=elements_vars
    )
    valence = get_material_valence(tmp_mat_obj, valence_cache=valence_cache)

Example: 

For detailed code please refer to example_advanced/example_advanced_reactions.py. The script examples_for_reactions.py read in our current database and add a new field `valence` in the `composition` field for each material as following. The returned value would be as following if the valence could be solved. The `valence` is a list because there could be multiple composition instances when there are variables in the formula. Each element in the `valence` filed is a dict which specify the valence state and values for variables. Sometimes, the valence state is not solved successfully. The value of `valence` would be None.

    'composition': [
        { 'amount': '1.0',
          'elements': {'Bi': 'x + 2.5', 'Na': '-x + 0.5', 'Nb': '2.0', 'O': '9.0'},
          'formula': 'Na0.5-xBi2.5+xNb2O9',
          'valence': [{'amounts_vars': [{'x': 0.05}],
                       'elements': [{'Bi': 2.55, 'Na': 0.45, 'Nb': 2.0, 'O': 9.0}],
                       'valence': {'Bi': 3.0, 'Na': 1.0, 'Nb': 4.95, 'O': -2.0}d},
                      {'amounts_vars': [{'x': 0.1}],
                       'elements': [{'Bi': 2.6, 'Na': 0.4, 'Nb': 2.0, 'O': 9.0}],
                       'valence': {'Bi': 3.0, 'Na': 1.0, 'Nb': 4.9, 'O': -2.0}}]}
    ]
    
