# Created by Wuli.Zuo a1785343
# 12/Oct/2019

from git import Repo, RemoteProgress
import os

# Function of git commands to identify VCC
def git_test_blame(local_link, fixing_commit):

    # Create repo object
    repo = Repo(local_link)

    # Reset to given commit
    repo.git.reset('--hard', fixing_commit)

    # Task 5: Compare results of different git.blame parameters
    # '-wCCC' is ignored because of the error: fatal: bad revision '–wCCC'

    parameters = ['-w', '-wM', '-wC', '-wCC']

    for parameter in parameters:

        # Frequencies of commits are calculated during Question a and b
        # Question a: identify the latest commit that modified each deleted line
        commits = []
        commits_count = []

        for file in repo.git.show('--name-only', '--format=').splitlines():  # Operate all the affected files one by one
            if file == "webapps/docs/changelog.xml" or file == "src/reference/asciidoc/whats-new.adoc":  # Ignore log files
                continue
            else:
                # print("\nFile: %s" % file)
                lines = repo.git.show(file).splitlines()
                line_count = 0
                start_line = 0

                file_blame_info_cur = repo.git.blame(fixing_commit, file).splitlines()

                # Catch error of new added file
                try:
                    file_blame_info_pre = repo.git.blame(fixing_commit + "^", file).splitlines()
                except:
                    pass
                finally:
                    # Find target commit of deleted lines
                    # print("\n(a). Find latest modifying commit for each deleted lines")
                    for line in lines:
                        if line.startswith("@@"):
                            temp_start = line.split()
                            temp_start = temp_start[1].split("-")
                            temp_start = temp_start[1].split(",")
                            start_line = int(temp_start[0])
                            # print("start line: %d" % start_line)
                            line_count = 0
                        else:
                            if start_line == 0:
                                continue
                            else:
                                if line.startswith("+"):
                                    continue
                                if line.startswith("-"):
                                    line_num = int(start_line) + int(line_count)
                                    # print("Deleted line: %d" % line_num)
                                    # For the deleted line, blame the previous commit
                                    blame_info = file_blame_info_pre[line_num - 1]
                                    target_commit = blame_info.split()[0]
                                    # print("Target commit for Line %d: %s" % (line_num, target_commit))
                                    if not target_commit in commits:
                                        commits.append(target_commit)
                                        commits_count.append(1)
                                    else:
                                        index = commits.index(target_commit)
                                        commits_count[index] += 1
                                    line_count += 1
                                else:
                                    line_count += 1

                    # Find target commit of added lines' smallest scope
                    # Find smallest scope for each added scope in current commit
                    # print("\n(b)-1. Find smallest scope for each added lines")

                    # Find all added lines
                    # Find first closest existing line in previous commit for the added line
                    line_count = 0
                    start_line_cur = 0
                    start_line_pre = 0
                    closest_line_count = 0
                    closest_lines_num = set()
                    pre_line_type = 0  # 1="-", 2="+", 3=none

                    for line in lines:
                        if line.startswith("@@"):
                            start_line_cur = line.split()
                            start_line_cur = start_line_cur[2].split("+")
                            start_line_cur = start_line_cur[1].split(",")
                            start_line_cur = int(start_line_cur[0])
                            # print("start line for current commit: %d" % start_line_cur)

                            start_line_pre = line.split()
                            start_line_pre = start_line_pre[1].split("-")
                            start_line_pre = start_line_pre[1].split(",")
                            start_line_pre = int(start_line_pre[0])
                            # print("start line for previous commit: %d" % start_line_cur)

                            line_count = 0
                            closest_line_count = 0
                        else:
                            if start_line_cur == 0:
                                continue
                            else:
                                if line.startswith("-"):
                                    # Find closest existing line num in previous commit
                                    closest_line_count += 1
                                    # print("closest_line_count++")
                                    pre_line_type = 1
                                    continue
                                if line.startswith("+"):
                                    line_num = int(start_line_cur) + int(line_count)
                                    # print("Added line: %d" % line_num)
                                    # added_lines.add(line)
                                    closest_existing_num = int(start_line_pre) + int(closest_line_count)
                                    if pre_line_type == 2:
                                        continue
                                    if pre_line_type == 3:
                                        closest_existing_num -= 1
                                        closest_line_count -= 1
                                    closest_lines_num.add(closest_existing_num)
                                    # print("Closest existing line: %d" % closest_existing_num)
                                    line_count += 1
                                    pre_line_type = 2
                                    # print("line_count++")
                                else:
                                    line_count += 1
                                    closest_line_count += 1
                                    pre_line_type = 3
                                    # print("closest_line_count & line_count ++")
                                # print("line_count = %d" % line_count)
                                # print("closest_lines_count = %d" % closest_line_count)

                    # Find smallest scope for each closest existing line for each added line
                    # Add lines in the smallest scope in set
                    lines_in_scope = set()

                    for line_num in closest_lines_num:
                        scope_begin_signs = 0
                        scope_end_signs = 0
                        scope_begin_line_num = line_num - 1
                        scope_end_line_num = line_num + 1

                        # Find scope begin line number in the previous commit
                        for i in range(1, line_num):
                            blame_info = file_blame_info_pre[line_num - i - 1].split()
                            # print("blame_info: %s" % blame_info)
                            code = blame_info[7:len(blame_info)]
                            code = " ".join(code)
                            # print("Line %d, Code content: %s" % (line_num-i,code))
                            if i == line_num - 1:
                                # scope_begin_line = code
                                scope_begin_line_num = 1
                            else:
                                scope_begin_signs += code.count("{")
                                scope_end_signs += code.count("}")
                                if scope_begin_signs > scope_end_signs:
                                    scope_begin_line_num = line_num - i
                                    # print("scope_begin_line of line %d: %s" % (line_num,scope_begin_line))
                                    break
                        # print("begin_line_num: %s" % scope_begin_line_num)

                        # Find scope end line number in the previous commit
                        if (scope_begin_line_num == 1):
                            scope_end_line_num = len(file_blame_info_pre)
                        else:
                            for i in range(line_num, len(file_blame_info_pre)):
                                blame_info = file_blame_info_pre[i - 1].split()
                                code = blame_info[7:len(blame_info)]
                                code = " ".join(code)
                                # print("Line %d, Code content: %s" % (line_num-i,code))
                                if i == len(file_blame_info_pre) - 1:
                                    # scope_begin_line = code
                                    scope_end_line_num = i
                                else:
                                    scope_begin_signs += code.count("{")
                                    scope_end_signs += code.count("}")
                                    if scope_begin_signs == scope_end_signs:
                                        scope_end_line_num = i
                                        break
                        # print("scope for line %d in the previous commit: %d, %d" % (line_num, scope_begin_line_num, scope_end_line_num))
                        for i in range(scope_begin_line_num, scope_end_line_num + 1):
                            if not i in lines_in_scope:
                                lines_in_scope.add(i)

                    # Find target commit for each line of the identified scope in previous commit
                    # print("\n(b)-2. Find target commit for each line in the scope")
                    for line_num in lines_in_scope:
                        blame_info = file_blame_info_pre[line_num - 1]
                        # print("blame info: %s" % blame_info)
                        target_commit = blame_info.split()[0]
                        # print("Target commit for line %d: %s" % (line_num, target_commit))
                        if not target_commit in commits:
                            commits.append(target_commit)
                            commits_count.append(1)
                        else:
                            index = commits.index(target_commit)
                            commits_count[index] += 1

        # Find most frequently identified commit as the VCC
        # print("\n(c). Select VCC")
        # print("All commits: %s" % commits)
        # print("Count of commits: %s" % commits_count)

        # Find most frequently identified commit as the VCC
        vcc = commits[commits_count.index(max(commits_count))]
        print("VCC with Parameter %s is: %s" % (parameter, vcc))

# main

class Progress(RemoteProgress):
    def update(self, op_code, cur_count, max_count=None, message=''):
        print(self._cur_line)

# Case 1
remote_link = "https://github.com/spring-projects/spring-amqp"
local_link = "../spring-amqp"
if not os.path.isdir(local_link):
    Repo.clone_from(remote_link, local_link, progress=Progress())
fixing_commit = "444b74e95bb299af5e23ebf006fbb45d574fb95"
print("\nOperation of repo: %s" % (remote_link))
git_test_blame(local_link, fixing_commit)

# Case 2
remote_link = "https://github.com/apache/pdfbox"
local_link = "../pdfbox"
if not os.path.isdir(local_link):
    Repo.clone_from(remote_link, local_link, progress=Progress())
fixing_commit = "4fa98533358c106522cd1bfe4cd9be2532af852"
print("\nOperation of repo: %s" % (remote_link))
git_test_blame(local_link, fixing_commit)

# Case 3
remote_link = "https://github.com/apache/tomcat80"
local_link = "../tomcat80"
if not os.path.isdir(local_link):
    Repo.clone_from(remote_link, local_link, progress=Progress())
fixing_commit = "ec10b8c785d1db91fe58946436f854dde04410fd"
print("\nOperation of repo: %s" % (remote_link))
git_test_blame(local_link, fixing_commit)