# Created by Wuli.Zuo a1785343
# 12/Oct/2019

from git import Repo, RemoteProgress
import os

# Analyse the summary line
def analyse_diff_summary(sum_line):
    sum_line = sum_line.split(' ')
    sum_del = sum_line[1].split(",")
    sum_add = sum_line[2].split(",")
    start_del = -int(sum_del[0])
    if len(sum_del) == 1:
        length_del = 1
    else:
        length_del = int(sum_del[1])
    start_add = int(sum_add[0])
    if len(sum_add) == 1:
        length_add = 1
    else:
        length_add = int(sum_add[1])
    return (start_del, length_del, start_add, length_add)

# find smallest cope for a line
def find_enclosing_scope(line_num, file_blame_info_pre):
    scope_sign = 0
    scope_begin_line_num = line_num
    scope_end_line_num = line_num + 1

    # Find scope begin line number in the previous commit
    for i in range(0, line_num):
        blame_info = file_blame_info_pre[line_num - i - 1].split()
        # print("blame_info: %s" % blame_info)
        code = blame_info[6:len(blame_info)]
        code = " ".join(code)
        # print("Line %d: %s" % (line_num - i, code))
        code = code[::-1]
        for c in code:
            if c == '}':
                scope_sign -= 1
            else:
                if c == '{':
                    scope_sign += 1
            if scope_sign == 1:
                scope_begin_line_num = line_num - i
                break
        # print("scope_sign = %d" % scope_sign)
        if scope_sign == 1:
            break
        if i == line_num - 1:
            return (0, 0)
    # print("begin_line_num: %s" % scope_begin_line_num)

    # Find scope end line number in the previous commit
    for i in range(line_num + 1, len(file_blame_info_pre) + 1):
        blame_info = file_blame_info_pre[i - 1].split()
        code = blame_info[6:len(blame_info)]
        code = " ".join(code)
        # print("Line %d, Code content: %s" % (line_num-i,code))
        for c in code:
            if c == '}':
                scope_sign -= 1
            else:
                if c == '{':
                    scope_sign += 1
            if scope_sign == 0:
                scope_end_line_num = i
                break
        if scope_sign == 0:
            break
    return (scope_begin_line_num, scope_end_line_num)

# find most recent commit for blames in a scope
def find_most_recent_commit(blames_info):
    latest = 0
    target_commit = ""
    for b in blames_info:
        # print("blame: %s" % b )
        b = b.split()
        commit = b[0]
        time = int(b[3])
        if time > latest:
            latest = time
            target_commit = commit
    return target_commit

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

        # Create repo object
        repo = Repo(local_link)

        # Reset to given commit
        repo.git.reset('--hard', fixing_commit)

        # Frequencies of commits are calculated during Question a and b
        commits = []
        commits_count = []

        # Operate all the affected files one by one
        for file in repo.git.show('--name-only', '--format=').splitlines():
            # print("\nFile: %s" % file)
            lines = repo.git.show('-U0', file).splitlines()

            # Catch error of new added files
            try:
                file_blame_info_pre = repo.git.blame('-w', '-f', '-e', '-t', fixing_commit + "^", file).splitlines()
            except:
                # print("%s is a new added file." % file)
                continue
            else:
                # Operate for each summary line
                for line in lines:
                    if line.startswith("@@"):
                        (start_del, length_del, start_add, length_add) = analyse_diff_summary(line)

                        # Question a: identify the latest commit that modified each deleted line
                        # For each deleted lines, find latest commit
                        for i in range(start_del, start_del + length_del):
                            # print("Deleted line: %d" % i)
                            blame_info = file_blame_info_pre[i - 1]
                            target_commit = blame_info.split()[0]
                            # print("Target commit: %s" % target_commit)
                            # Count commit
                            if target_commit in commits:
                                index = commits.index(target_commit)
                                commits_count[index] += 1
                            else:
                                commits.append(target_commit)
                                commits_count.append(1)

                        # Question b: identify the latest commit that modified lines in the the smallest enclosing scope of each added line
                        # For added lines, find the smallest enclosing scope
                        # for i in range(start_add, start_add + length_add):
                            # print("Added line: %d" % i)
                        (scope_begin_line_num, scope_end_line_num) = find_enclosing_scope(start_del,
                                                                                          file_blame_info_pre)
                        if not scope_begin_line_num == 0:
                            blames_info = file_blame_info_pre[scope_begin_line_num - 1: scope_end_line_num]
                            target_commit = find_most_recent_commit(blames_info)
                            # print("scope in the previous commit: %d, %d" % (scope_begin_line_num, scope_end_line_num))
                        else:
                            target_commit = 'skip'
                            # print("scope in the previous commit: whole file")
                        # print("Target commit: %s" % target_commit)

                        # Count commit * length_add
                        if target_commit in commits:
                            index = commits.index(target_commit)
                            commits_count[index] += length_add
                        else:
                            commits.append(target_commit)
                            commits_count.append(length_add)

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