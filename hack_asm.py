"""
This script reads .asm files written in HACK assembly symbolic language
and then creates a new .hack file with a binary representation of the code.
"""

import os


def parser(file_loc):
    """
    Inputs:
        file_loc - location of file to read
    Output:
        parced_lst - parced list of lines-strings from the file

        Each line will be a single line string with no ('\n'), ('\r') or ('\t') characters.
        Comments starting with ('//') are detected and ignored, as well as empty lines.
    """

    # open, read the text file and then break it into lines
    with open(file_loc, 'r', encoding='utf-8') as input_file:
        asm_lst = input_file.read().splitlines()
    
    # parse the list (whitespaces, empty lines and comments are ignored)
    parsed_lst = []
    for line in asm_lst:
        if line != '':
            # eliminate whitespaces
            mod_line = "".join(line.split())
            # delete comments
            if '/' in mod_line:
                ind = mod_line.index("/")
                if ind != 0:
                    mod_line = mod_line[0:ind]
                    parsed_lst.append(mod_line)
            else:
                parsed_lst.append(mod_line)

    return parsed_lst


def label_table (instr_lst):
    """
    Inputs: instr_lst - parsed list
    Output: table_dict - a label table with labels as keys 
    and following instruction numbers as values.

    Mutates the (instr_lst) by deleting all lines containing labels.
    """
    table_dict = {}
    instr_count = 0

    # loop through a copy of the list
    for line in instr_lst.copy():
        # in case of a normal instruction, update the counter
        if '(' not in line:
            instr_count += 1
        # if label expression is found, update the table 
        # and remove the line from the original list
        else:
            label = line[1:-1]
            table_dict[label] = instr_count
            instr_lst.remove(line)

    return table_dict
        

def const_table():
    """
    Input: none
    Output: a pre-defined table of values for constants
    specified by the HACK language.
    """
    table_dict = {}

    for i in range (16):
        symb = 'R' + str(i)
        table_dict[symb] = i

    table_dict['SCREEN'] = 16384
    table_dict['KBD'] = 24576

    table_dict['SP'] = 0
    table_dict['LCL'] = 1
    table_dict['ARG'] = 2
    table_dict['THIS'] = 3
    table_dict['THAT'] = 4

    return table_dict


def var_table (instr_lst, lbl_tbl, const_tbl):
    """
    Inputs: instruction list, tables with labels and constants
    Output: table-dictionary with names of variables as keys
    and their RAM addresses as values

    Does not mutate (instr_lst)
    """
    table_dict = {}
    ram_pointer = 16

    for line in instr_lst:
        if line[0] == '@':
            if not line[1].isdigit():
                symb = line[1:]
                if symb not in lbl_tbl.keys() and symb not in const_tbl.keys() and symb not in table_dict.keys():
                    table_dict[symb] = ram_pointer
                    ram_pointer += 1
    
    return table_dict


def refer_to_num(instr_lst, lbl_tbl, const_tbl, var_tbl):
    """
    Inputs: 3 tables for symbols and instruction list
    Output: new instruction list without references

    Iterates through the list and substitutes every symbol found
    with a respective value from one of the tables
    """

    symb_tbl = {**lbl_tbl, **const_tbl, **var_tbl}

    new_lst = []

    for line in instr_lst:
        if line[0] == '@':
            if not line[1].isdigit():
                symb = line[1:]
                new_line = '@' + str(symb_tbl[symb])
                new_lst.append(new_line)
            else:
                new_lst.append(line)
        else:
            new_lst.append(line)

    return new_lst


def a_instr_encoder(instr):
    """
    Input: A-type instruction in HACK assembly language (string)
    Output: Corresponding 16-bit binary command (string)

    Every A-instruction obeys the formal formatting of type:
    @decimal_number
    """
    bin_str = bin(int(instr[1:]))[2:]
    for _ in range(16 - len(bin_str)):
        bin_str = '0' + bin_str

    return bin_str


def c_instr_encoder(line, comp_tbl, dest_tbl, jmp_tbl):
    """
    Input: C-type instruction in HACK assembly language (string)
    Output: Corresponding 16-bit binary command (string)

    Every C-instruction obeys the formal formatting of type:
    destination = computation ; jump condition 
    """
    ind_eq = - len(line) - 1
    if '=' in line:
        ind_eq = line.index('=')

    ind_jmp = len(line)
    if ';' in line:
        ind_jmp = line.index(';')

    dest = line[:ind_eq]
    if dest == '':
        dest = 'null'

    jmp = line[ind_jmp + 1:]
    if jmp == '':
        jmp = 'null'

    comp = line[ind_eq + 1:ind_jmp]

    return '111' + comp_tbl[comp] + dest_tbl[dest] + jmp_tbl[jmp]


def bin_encoder(instr_lst):
    """
    Input: a list of instructions in HACK assembly language
    with all the references (labels, constants, variables)
    substituted with real values from the previous tables.
    Output: a list of binary instructions that can be loaded
    directly into HACK ROM memory and executed.
    """

    # create a binary table for 'computation'
    # part of c-instruction
    comp_tbl = {}
    comp_tbl['0'] = '0101010'
    comp_tbl['1'] = '0111111'
    comp_tbl['-1'] = '0111010'
    comp_tbl['D'] = '0001100'
    comp_tbl['A'] = '0110000'
    comp_tbl['M'] = '1110000'
    comp_tbl['!D'] = '0001101'
    comp_tbl['!A'] = '0110001'
    comp_tbl['!M'] = '1110001'
    comp_tbl['-D'] = '0001101'
    comp_tbl['-A'] = '0110011'
    comp_tbl['-M'] = '1110011'
    comp_tbl['D+1'] = '0011111'
    comp_tbl['A+1'] = '0110111'
    comp_tbl['M+1'] = '1110111'
    comp_tbl['D-1'] = '0001110'
    comp_tbl['A-1'] = '0110010'
    comp_tbl['M-1'] = '1110010'
    comp_tbl['D+A'] = '0000010'
    comp_tbl['D+M'] = '1000010'
    comp_tbl['D-A'] = '0010011'
    comp_tbl['D-M'] = '1010011'
    comp_tbl['A-D'] = '0000111'
    comp_tbl['M-D'] = '1000111'
    comp_tbl['D&A'] = '0000000'
    comp_tbl['D&M'] = '1000000'
    comp_tbl['D|A'] = '0010101'
    comp_tbl['D|M'] = '1010101'

    # create a binary table for 'destination'
    # part of c-instruction
    dest_tbl = {}
    dest_tbl['null'] = '000'
    dest_tbl['M'] = '001'
    dest_tbl['D'] = '010'
    dest_tbl['MD'] = '011'
    dest_tbl['A'] = '100'
    dest_tbl['AM'] = '101'
    dest_tbl['AD'] = '110'
    dest_tbl['AMD'] = '111'

    # create a binary table for 'jump'
    # part of c-instruction
    jmp_tbl = {}
    jmp_tbl['null'] = '000'
    jmp_tbl['JGT'] = '001'
    jmp_tbl['JEQ'] = '010'
    jmp_tbl['JGE'] = '011'
    jmp_tbl['JLT'] = '100'
    jmp_tbl['JNE'] = '101'
    jmp_tbl['JLE'] = '110'
    jmp_tbl['JMP'] = '111'

    bin_lst = []
    for line in instr_lst:
        if line[0] == '@':
            bin_line = a_instr_encoder(line)
        else:
            bin_line = c_instr_encoder(line, comp_tbl, dest_tbl, jmp_tbl)
        bin_lst.append(bin_line)

    return bin_lst


def main(user_input):

    # computing paths to internal directories
    curr_dir = os.getcwd()
    asm_dir = os.path.join(curr_dir, 'ASM_instructions')
    bin_dir = os.path.join(curr_dir, 'HACK_machine_code')
    
    # computing absolute path to the .asm and .hack files
    asm_filename = user_input + '.asm'
    bin_filename = user_input + '.hack'
    asm_file_loc = os.path.join(asm_dir, asm_filename)
    bin_file_loc = os.path.join(bin_dir, bin_filename)

    # parse the original text into the list of strings-ASM commands
    instr_lst = parser(asm_file_loc)

    # create 3 temporary tables for all references
    lbl_tbl = label_table(instr_lst)
    const_tbl = const_table()
    var_tbl = var_table(instr_lst, lbl_tbl, const_tbl)

    # translate each reference into its numeric value
    instr_lst = refer_to_num(instr_lst, lbl_tbl, const_tbl, var_tbl)

    # encode each string-line into its binary equivalent
    bin_lst = bin_encoder(instr_lst)

    # write the result to the file
    with open(bin_file_loc, 'w', encoding='utf-8') as out_f:
        for line in bin_lst:
            out_f.write("%s\n" % line)
     

if __name__ == '__main__':

    print('\n<<< SCRIPT START >>>\n')

    # ask user to choose the .asm file for assembling
    user_input = input('Enter the name of the file for translation into machine code\n')
    main(user_input)

    print('\n<<< SCRIPT END >>>\n')