
import copy
import os
import sys
import argparse

def combine_requirements(files, output_path='/tmp/requirements.txt'):
    """
    @params files: list of filenames in requirements.txt format
    @returns: union, intersection, duplicates, version_diffs
    """
    lines = {}
    union = {}
    intersection = {}
    duplicates = {}
    version_diffs = {}
    file_versions_map = {}
    for _file in files:
        print('_file', _file)
        with open(_file, 'r') as f:
            _file = os.path.basename(_file)
            file_versions_map[_file] = {}
            lines[_file] = f.readlines()
            for line in lines[_file]:
                if line.startswith('#') or (len(line.strip()) == 0):
                    print('skipping line with contents {}'.format(line))
                    continue
                try:
                    package, version = get_package_info(line)
                except ValueError as err:
                    raise(ValueError(" : ".join([err.message, line])))
                existing_list = union.get(package, [])
                new_list = copy.copy(existing_list)
                new_list.append((version, _file))
                union.update({package: new_list})
                file_versions_map[_file].update({package: (version, line)})
                for (existing_version, existing_file) in existing_list:
                    print(existing_version, existing_file)
                    if existing_version == version:
                        if package not in duplicates:
                            duplicates[package] = [(existing_version, existing_file), (version, _file)]
                        else:
                            #print(duplicates.keys())
                            duplicates.get(package).append((version, _file))
                    else:
                        if version_diffs.get(package, None):
                            version_diffs.get(package, []).append((version, _file))
                        else:            
                            version_diffs[package] = [(existing_version, existing_file), (version, _file)]
                                                           
    intersection = set(union.keys())
    # conservative intersection, do not include same package with different versions
    for _file in files:
        _file = os.path.basename(_file)
        intersection = intersection.intersection(set(file_versions_map[_file].keys()))
        orig_intersection = copy.copy(intersection)
        # remove packages with different versions
        for package, info in file_versions_map[_file].items():
            version, line = info
            if package in orig_intersection.intersection(set(version_diffs.keys())):
                print("Removing package {} with different versions {}".format(
                    package, version_diffs[package]))
                intersection.remove(package)
                                                           

    out_lines = []
    for _file in file_versions_map.keys():
        out_lines.append('\n# ' + _file + '\n\n')
        for package, info in file_versions_map[_file].items():
            version, line = info
            if package in duplicates.keys():
                out_lines.append('# ' + line.strip() +  ' (duplicate)\n')
            elif package in version_diffs.keys():
                out_lines.append('# ' + line.strip() + ' (version_diff)\n')
            else:
                out_lines.append(line)
        
    with open(output_path, 'w') as f:
        f.writelines(out_lines)
        
    return union, intersection, version_diffs, duplicates
                
        
def get_package_info(line):
    """
    @param line: a line from a requirements.txt file
    WARNING: currently only supports '==' not '<=, ~=, etc'
    examples:
      foo==1.0.1
      foo
      [-e] git+git://git.myproject.org/SomeProject#egg=SomeProject
      [-e] git+https://git.myproject.org/SomeProject#egg=SomeProject
      [-e] git+ssh://git.myproject.org/SomeProject#egg=SomeProject
      [-e] git://git.myproject.org/MyProject.git@master#egg=MyProject
      [-e] git://git.myproject.org/MyProject.git@v1.0#egg=MyProject
      [-e] git://git.myproject.org/MyProject.git@da39a3ee5e6b4b0d3255bfef95601890afd80709#egg=MyProject
    """
    if line.startswith('-e') or line.startswith('[-e'):
        if line.find('#egg=') != -1:
            prefix, package = line.strip().split('#egg=')
            # set a default version
            version = 'master-latest'
        else:
            raise ValueError("unrecognized format for line {}\n expected '#egg=<python-package>'".format(line))
        if prefix.find('@') != -1:
            version = prefix.split('@')[1]
    else:
        split = line.split('==')
        package = split[0].strip()
        if len(split) == 2:
            version = split[1].strip()
        elif len(split) == 1:
            version = 'latest'
        else:
            raise(ValueError('unrecognized requirements.txt line {}'.format(line)))
    if len(package) == 0:
        raise(ValueError('un-recognized version for line {}'.format(line)))
    return package, version
            
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("method")
    parser.add_argument("-f", "--files", help="comma separated no spaces list of files to process")
    parser.add_argument("-o", "--output-path",
                        help="comma separated no spaces list of files to process",
                        default="/tmp/requirements.txt")
    args = parser.parse_args()    
        
    if args.method == 'combine_requirements':
        files = args.files.split(',')
        combine_requirements(files, output_path=args.output_path)
    
if __name__ == '__main__':
    main()
    