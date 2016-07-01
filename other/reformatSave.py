file_handle = open('info/save.data', 'r')
lines = file_handle.readlines()
file_handle.close()
new_lines = []
for line in lines:
    temp_list = line.replace('\n', '').split('\t')
    new_list = list([])
    new_list.append(temp_list[0])
    new_list.append(temp_list[2])
    new_list.append(temp_list[1])
    new_lines.append('\t'.join(new_list))

file_handle = open('info/new.data', 'w')
file_handle.write('\n'.join(new_lines))
file_handle.close()