# -*- coding: utf-8 -*-
# Import Python libs
from __future__ import absolute_import, print_function, unicode_literals
import os
import re
import logging
from jinja2 import FileSystemLoader, Environment

# Import Salt libs
import salt.utils.path
import salt.utils.yaml
from salt.exceptions import SaltException

# Import 3rd-party libs
from salt.ext import six

# No need to invent bicycle
from collections import deque, OrderedDict

log = logging.getLogger(__name__)


# Renders jinja from a template file
def render_jinja(_file, salt_data):
    j_env = Environment(loader=FileSystemLoader(os.path.dirname(_file)))
    j_env.globals.update({
        '__opts__': salt_data['__opts__'],
        '__salt__': salt_data['__salt__'],
        '__grains__': salt_data['__grains__'],
        '__pillar__': salt_data['__pillar__'],
        'minion_id': salt_data['minion_id'],
    })
    j_render = j_env.get_template(os.path.basename(_file)).render()
    return j_render


# Renders yaml from rendered jinja
def render_yaml(_file, salt_data):
    return salt.utils.yaml.safe_load(render_jinja(_file, salt_data))


# Returns a dict from a class yaml definition
def get_class(_class, salt_data):
    l_files = []
    saltclass_path = salt_data['path']

    straight = os.path.join(saltclass_path,
                            'classes',
                            '{0}.yml'.format(_class))
    sub_straight = os.path.join(saltclass_path,
                                'classes',
                                '{0}.yml'.format(_class.replace('.', os.sep)))
    sub_init = os.path.join(saltclass_path,
                            'classes',
                            _class.replace('.', os.sep),
                            'init.yml')

    for root, dirs, files in salt.utils.path.os_walk(os.path.join(saltclass_path, 'classes'), followlinks=True):
        for l_file in files:
            l_files.append(os.path.join(root, l_file))

    if straight in l_files:
        return render_yaml(straight, salt_data)

    if sub_straight in l_files:
        return render_yaml(sub_straight, salt_data)

    if sub_init in l_files:
        return render_yaml(sub_init, salt_data)

    log.warning('%s: Class definition not found', _class)
    return {}


# Return environment
def get_env_from_dict(exp_dict_list):
    environment = ''
    for s_class in exp_dict_list:
        if 'environment' in s_class:
            environment = s_class['environment']
    return environment


# Merge dict b into a
def dict_merge(a, b, path=None, reverse=False):
    if path is None:
        path = []

    for key in b:
        if key in a:
            if isinstance(a[key], list) and isinstance(b[key], list):
                if not reverse:
                    if b[key][0] == '^':
                        b[key].pop(0)
                        a[key] = b[key]
                    else:
                        a[key].extend(b[key])
                else:
                    # если в листе, куда мержим, уже есть ^
                    # то не делаем ничего
                    if a[key][0] == '^':
                        pass
                    # если нет, то мержим в начало
                    else:
                        a[key][0:0] = b[key]
            elif isinstance(a[key], dict) and isinstance(b[key], dict):
                dict_merge(a[key], b[key], path + [six.text_type(key)], reverse=reverse)
            elif a[key] == b[key]:
                pass
            else:
                # если мы здесь, то у ключей в a и b разные типы
                # в случае reverse обновляем, тк проход происходит в направлении generic -> specific
                if not reverse:
                    a[key] = b[key]
                # в случае не reverse не трогаем, тк проход происходит в направлении specific -> generic
                # и в a[key] уже более правильные данные
                else:
                    pass
        else:
            a[key] = b[key]
    return a


# Recursive search and replace in a dict
def dict_search_and_replace(d, old, new, expanded):
    for (k, v) in six.iteritems(d):
        if isinstance(v, dict):
            dict_search_and_replace(d[k], old, new, expanded)

        if isinstance(v, list):
            x = 0
            for i in v:
                if isinstance(i, dict):
                    dict_search_and_replace(v[x], old, new, expanded)
                if isinstance(i, six.string_types):
                    if i == old:
                        v[x] = new
                x = x + 1

        if v == old:
            d[k] = new

    return d


# Retrieve original value from ${xx:yy:zz} to be expanded
def find_value_to_expand(x, v):
    a = x
    for i in v[2:-1].split(':'):
        if a is None:
            return v
        if i in a:
            a = a.get(i)
        else:
            return v
    return a


# Look for regexes and expand them
def find_and_process_re(_str, v, k, b, expanded):
    vre = re.finditer(r'(^|.)\$\{.*?\}', _str)
    if vre:
        for re_v in vre:
            re_str = str(re_v.group())
            if re_str.startswith('\\'):
                v_new = _str.replace(re_str, re_str.lstrip('\\'))
                b = dict_search_and_replace(b, _str, v_new, expanded)
                expanded.append(k)
            elif not re_str.startswith('$'):
                v_expanded = find_value_to_expand(b, re_str[1:])
                v_new = _str.replace(re_str[1:], v_expanded)
                b = dict_search_and_replace(b, _str, v_new, expanded)
                _str = v_new
                expanded.append(k)
            else:
                v_expanded = find_value_to_expand(b, re_str)
                # TODO: refactor is badly needed here!
                if isinstance(v_expanded, list) or isinstance(v_expanded, dict):
                    v_new = v_expanded
                # Have no idea why do we need two variables of the same - _str and v
                elif isinstance(v, six.string_types):
                    v_new = v.replace(re_str, v_expanded)
                else:
                    v_new = _str.replace(re_str, v_expanded)
                b = dict_search_and_replace(b, _str, v_new, expanded)
                _str = v_new
                v = v_new
                expanded.append(k)
    return b


# Return a dict that contains expanded variables if found
def expand_variables(a, b, expanded, path=None):
    if path is None:
        b = a.copy()
        path = []

    for (k, v) in six.iteritems(a):
        if isinstance(v, dict):
            expand_variables(v, b, expanded, path + [six.text_type(k)])
        else:
            if isinstance(v, list):
                for i in v:
                    if isinstance(i, dict):
                        expand_variables(i, b, expanded, path + [str(k)])
                    if isinstance(i, six.string_types):
                        b = find_and_process_re(i, v, k, b, expanded)

            if isinstance(v, six.string_types):
                b = find_and_process_re(v, v, k, b, expanded)
    return b


def validate(name, data):
    if 'classes' in data:
        data['classes'] = [] if data['classes'] is None else data['classes']  # None -> []
        if not isinstance(data['classes'], list):
            raise SaltException('Classes in {} is not a valid list'.format(name))
    if 'pillars' in data:
        data['pillars'] = {} if data['pillars'] is None else data['pillars']  # None -> {}
        if not isinstance(data['pillars'], dict):
            raise SaltException('Pillars in {} is not a valid dict'.format(name))
    if 'states' in data:
        data['states'] = [] if data['states'] is None else data['states']  # None -> []
        if not isinstance(data['states'], list):
            raise SaltException('States in {} is not a valid list'.format(name))
    if 'environment' in data:
        data['environment'] = '' if data['environment'] is None else data['environment']  # None -> ''
        if not isinstance(data['environment'], six.string_types):
            raise SaltException('Environment in {} is not a valid string'.format(name))
    return


def get_saltclass_data(node_data, salt_data):
    # Merge minion_pillars into salt_data
    dict_merge(salt_data['__pillar__'], node_data.get('pillars', {}))

    # Init classes list with data from minion
    classes = deque(reversed(node_data.get('classes', [])))

    seen_classes = set()
    expanded_classes = OrderedDict()

    #
    # Build expanded_classes OrderedDict (we'll need it later)
    # and pillars dict for a minion
    #
    while classes:
        cls = classes.pop()
        seen_classes.add(cls)
        expanded_class = get_class(cls, salt_data)
        validate(cls, expanded_class)
        expanded_classes[cls] = expanded_class
        if 'pillars' in expanded_class and expanded_class['pillars'] is not None:
            dict_merge(salt_data['__pillar__'], expanded_class['pillars'], reverse=True)
        if 'classes' in expanded_class:
            for c in reversed(expanded_class['classes']):
                if c not in seen_classes and c not in classes:
                    classes.appendleft(c)

    # Get ordered class and state lists from expanded_classes and minion_classes (traverse expanded_classes tree)
    def traverse(this_class, result_list):
        result_list.append(this_class)
        leafs = expanded_classes.get(this_class, {}).get('classes', [])
        for leaf in leafs:
            traverse(leaf, result_list)

    # Start with node_data classes again, since we need to retain order
    ordered_class_list = []
    for cls in node_data.get('classes', []):
        traverse(cls, ordered_class_list)

    # Remove duplicates
    tmp = []
    for cls in reversed(ordered_class_list):
        if cls not in tmp:
            tmp.append(cls)
    ordered_class_list = tmp[::-1]

    # Build state list and get 'environment' variable
    ordered_state_list = node_data.get('states', [])
    environment = ''
    for cls in ordered_class_list:
        class_states = expanded_classes.get(cls, {}).get('states', [])
        if not environment:
            environment = expanded_classes.get(cls, {}).get('environment', '')
        for state in class_states:
            # Ignore states with override (^) markers in it's names
            # Do it here because it's cheaper
            if state not in ordered_state_list and state.find('^') == -1:
                ordered_state_list.append(state)

    # Expand ${xx:yy:zz} here and pop override (^) markers
    salt_data['__pillar__'] = expand_variables(pop_override_markers(salt_data['__pillar__']), {}, [])
    salt_data['__classes__'] = ordered_class_list
    salt_data['__states__'] = ordered_state_list
    return salt_data['__pillar__'], salt_data['__classes__'], salt_data['__states__'], environment


def expand_classes_in_order(minion_dict,
                            salt_data,
                            seen_classes,
                            expanded_classes,
                            classes_to_expand):
    # Get classes to expand from minion dictionary
    if not classes_to_expand and 'classes' in minion_dict:
        classes_to_expand = minion_dict['classes']

    # Now loop on list to recursively expand them
    for klass in classes_to_expand:
        if klass not in seen_classes:
            seen_classes.append(klass)
            expanded_classes[klass] = get_class(klass, salt_data)
            # Fix corner case where class is loaded but doesn't contain anything
            if expanded_classes[klass] is None:
                expanded_classes[klass] = {}

            # Now replace class element in classes_to_expand by expansion
            if expanded_classes[klass].get('classes'):
                l_id = classes_to_expand.index(klass)
                classes_to_expand[l_id:l_id] = expanded_classes[klass]['classes']
                expand_classes_in_order(minion_dict,
                                        salt_data,
                                        seen_classes,
                                        expanded_classes,
                                        classes_to_expand)
            else:
                expand_classes_in_order(minion_dict,
                                        salt_data,
                                        seen_classes,
                                        expanded_classes,
                                        classes_to_expand)

    # We may have duplicates here and we want to remove them
    tmp = []
    for t_element in classes_to_expand:
        if t_element not in tmp:
            tmp.append(t_element)

    classes_to_expand = tmp

    # Now that we've retrieved every class in order,
    # let's return an ordered list of dicts
    ord_expanded_classes = []
    ord_expanded_states = []
    for ord_klass in classes_to_expand:
        ord_expanded_classes.append(expanded_classes[ord_klass])
        # And be smart and sort out states list
        # Address the corner case where states is empty in a class definition
        if 'states' in expanded_classes[ord_klass] and expanded_classes[ord_klass]['states'] is None:
            expanded_classes[ord_klass]['states'] = {}

        if 'states' in expanded_classes[ord_klass]:
            ord_expanded_states.extend(expanded_classes[ord_klass]['states'])

    # Add our minion dict as final element but check if we have states to process
    if 'states' in minion_dict and minion_dict['states'] is None:
        minion_dict['states'] = []

    if 'states' in minion_dict:
        ord_expanded_states.extend(minion_dict['states'])

    ord_expanded_classes.append(minion_dict)

    return ord_expanded_classes, classes_to_expand, ord_expanded_states


def get_node_data(minion_id, salt_data):
    _file = ''
    saltclass_path = salt_data['path']
    # Start
    for root, dirs, files in salt.utils.path.os_walk(os.path.join(saltclass_path, 'nodes'), followlinks=True):
        for minion_file in files:
            if minion_file == '{0}.yml'.format(minion_id):
                _file = os.path.join(root, minion_file)

    # Load the minion_id definition if existing, else an empty dict

    if _file:
        result = render_yaml(_file, salt_data)
        validate(minion_id, result)
        return result
    else:
        log.info('%s: Node definition not found in saltclass', minion_id)
        return {}


def expanded_dict_from_minion(minion_id, salt_data):
    _file = ''
    saltclass_path = salt_data['path']
    # Start
    for root, dirs, files in salt.utils.path.os_walk(os.path.join(saltclass_path, 'nodes'), followlinks=True):
        for minion_file in files:
            if minion_file == '{0}.yml'.format(minion_id):
                _file = os.path.join(root, minion_file)

    # Load the minion_id definition if existing, else an empty dict
    node_dict = {}
    if _file:
        node_dict[minion_id] = render_yaml(_file, salt_data)
    else:
        log.info('%s: Node definition not found in saltclass', minion_id)
        node_dict[minion_id] = {}



    # Merge newly found pillars into existing ones
    dict_merge(salt_data['__pillar__'], node_dict[minion_id].get('pillars', {}))




    # Get 2 ordered lists:
    # expanded_classes: A list of all the dicts
    # classes_list: List of all the classes
    expanded_classes, classes_list, states_list = expand_classes_in_order(
                                                    node_dict[minion_id],
                                                    salt_data, [], {}, [])


    # Here merge the pillars together
    pillars_dict = {}
    for exp_dict in expanded_classes:
        if 'pillars' in exp_dict:
            dict_merge(pillars_dict, exp_dict)

    return expanded_classes, pillars_dict, classes_list, states_list


def pop_override_markers(b):
    if isinstance(b, list):
        if len(b) > 0 and b[0] == '^':
            b.pop(0)
        elif len(b) > 0 and b[0] == r'\^':
            b[0] = '^'
        for sub in b:
            pop_override_markers(sub)
    elif isinstance(b, dict):
        for sub in b.values():
            pop_override_markers(sub)
    return b


def new_get_pillars(minion_id, salt_data):
    node_data = get_node_data(minion_id, salt_data)
    pillars, classes, states, environment = get_saltclass_data(node_data, salt_data)

    # Build the final pillars dict
    pillars_dict = dict()
    pillars_dict['__saltclass__'] = {}
    pillars_dict['__saltclass__']['states'] = states
    pillars_dict['__saltclass__']['classes'] = classes
    pillars_dict['__saltclass__']['environment'] = environment
    pillars_dict['__saltclass__']['nodename'] = minion_id
    pillars_dict.update(pillars)

    return pillars_dict

def new_get_tops(minion_id, salt_data):
    node_data = get_node_data(minion_id, salt_data)
    _, _, states, environment = get_saltclass_data(node_data, salt_data)

    tops = dict()
    tops[environment] = states

    return tops


def get_pillars(minion_id, salt_data):
    # Get 2 dicts and 2 lists
    # expanded_classes: Full list of expanded dicts
    # pillars_dict: dict containing merged pillars in order
    # classes_list: All classes processed in order
    # states_list: All states listed in order
    (expanded_classes,
     pillars_dict,
     classes_list,
     states_list) = expanded_dict_from_minion(minion_id, salt_data)

    # Retrieve environment
    environment = get_env_from_dict(expanded_classes)

    # Expand ${} variables in merged dict
    # pillars key shouldn't exist if we haven't found any minion_id ref
    if 'pillars' in pillars_dict:
        pillars_dict_expanded = expand_variables(pop_override_markers(pillars_dict['pillars']), {}, [])
    else:
        pillars_dict_expanded = expand_variables({}, {}, [])

    # Build the final pillars dict
    pillars_dict = {}
    pillars_dict['__saltclass__'] = {}
    pillars_dict['__saltclass__']['states'] = states_list
    pillars_dict['__saltclass__']['classes'] = classes_list
    pillars_dict['__saltclass__']['environment'] = environment
    pillars_dict['__saltclass__']['nodename'] = minion_id
    pillars_dict.update(pillars_dict_expanded)

    return pillars_dict


def get_tops(minion_id, salt_data):
    # Get 2 dicts and 2 lists
    # expanded_classes: Full list of expanded dicts
    # pillars_dict: dict containing merged pillars in order
    # classes_list: All classes processed in order
    # states_list: All states listed in order
    (expanded_classes,
     pillars_dict,
     classes_list,
     states_list) = expanded_dict_from_minion(minion_id, salt_data)

    # Retrieve environment
    environment = get_env_from_dict(expanded_classes)

    # Build final top dict
    tops_dict = {}
    tops_dict[environment] = states_list

    return tops_dict
