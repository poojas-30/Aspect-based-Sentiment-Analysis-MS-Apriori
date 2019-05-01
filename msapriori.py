# MS Apriori implementation

import sys
import math
import itertools

transactions = []
cannot_constraint = []
must_have = []
mis = {}


# Take input
def input():
    if len(sys.argv) < 4:
        print("Pass input, parameter and output files as arguments. Format - python msapriori.py input.txt parameter.txt output.txt")
        sys.exit(0)

    input_file = open(sys.argv[1], 'r')
    parameter_file = open(sys.argv[2], 'r')
    for line in input_file:
        line = line.strip()[1:-1]
        data = line.split(', ')
        transactions.append(data)

    for line in parameter_file:
        if line.find('MIS') is not -1:
            item = line[line.find('(')+1:line.find(')')]
            mis_val = line[line.find('=')+1:].strip()
            mis[item] = mis_val

        elif line.find('SDC') is not -1:
            global sdc_val
            sdc_val = line[line.find('=')+1:].strip()

        elif line.find('cannot_be_together') is not -1:
            line = line.split(':')[1].strip()
            while line.find('{') is not -1:
                open_pos = line.find('{')
                close_pos = line.find('}')
                itemset = line[open_pos+1:close_pos]
                cannot_constraint.append(itemset.split(', '))
                line = line[close_pos+1:]

        elif line.find('must-have') is not -1:
            line = line.split(':')[1].strip()
            items = line.split(' or ')
            must_have.extend(items)

    input_file.close()
    parameter_file.close()


def calc_support(item, transactions):
    total = sum(x.count(item) for x in transactions)
    return total/len(transactions)


def calc_count(item, transactions):
    total = 0
    for transaction in transactions:
        if item.issubset(transaction):
            total += 1
    return total


def must_have_constraint(Fk):
    if len(must_have) == 0:
        return Fk
    valid = []
    for item in Fk:
        if isinstance(item, (list,)):
            set1 = set(item)
        else:
            set1 = {item}
        if len(set1.intersection(set(must_have))) is not 0:
            valid.append(item)
    return valid


def cannot_have_constraint(Fk):
    if len(cannot_constraint) == 0:
        return Fk
    result = []
    for item in cannot_constraint:
        for item2 in Fk:
            if set(item).issubset(set(item2)):
                if item2 not in result :
                    result.append(item2)
    for item in result:
        Fk.remove(item)
    return Fk


# init-pass to generate the Frequent 1 candidate set
def init_pass(M, transactions):
    global F
    L = []
    F1 = []
    F = []
    i = None
    for item in M:
        sup = calc_support(item, transactions)
        if i is None and sup < float(mis[item]):
            continue
        else:
            if i is None:
                L.append(item)
                if sup >= float(mis[item]):
                    F1.append(item)
                i = item
            else:

                sup = calc_support(item,transactions)
                if sup >= float(mis[i]):
                    L.append(item)
                if sup >= float(mis[item]):
                    F1.append(item)

    #F1 = must_have_constraint(F1)
    #F1 = cannot_have_constraint(F1)
    F.append(F1)
    return L


def candidate_2_gen(L):
    C2 = []
    for item in L:
        if calc_support(item,transactions) >= float(mis[item]):
            for i in range(L.index(item)+1, len(L)):
                sup_i = calc_support(L[i], transactions)
                sup_item = calc_support(item, transactions)
                if (sup_i >= float(mis[item])) and (math.fabs(sup_i-sup_item) <= float(sdc_val)):
                    C2.append([item, L[i]])
    return C2


def candidate_gen(Fk_1):
    Ck = []
    for f1 in Fk_1:
        for f2 in Fk_1:
            if f1 != f2:
                if f1[0:-1] == f2[0:-1]:
                    c = list(f1)
                    c.append(f2[-1])
                    if float(f1[-1]) < float(f2[-1]) and c not in Ck and math.fabs(
                            calc_support(f1[-1], transactions) - calc_support(f2[-1], transactions)) <= float(sdc_val):
                        s = itertools.combinations(c, len(c) - 1)
                        Ck.append(c)
                        for subset_k_1 in s:
                            if {c[0]}.issubset(set(subset_k_1)) or (mis[c[1]] == mis[c[0]]):
                                if list(subset_k_1) not in Fk_1:
                                    Ck.remove(c)
                                    break
    return Ck


def ms_apriori():
    Ck = []
    M = [x[0] for x in sorted(mis.items(), key = lambda x: x[1])]
    L = init_pass(M,transactions)
    tail_count_dict = {}

    if len(L) is not 0:
        for k in range(1, len(mis)):
            if k > len(F) or len(F[k-1]) is 0:
                break;
            else:
                if k == 1:
                    Ck = candidate_2_gen(L)
                else:
                    Ck = candidate_gen(F[k-1])

                Fk = []
                for c in Ck:
                    count = 0
                    tail_count = 0
                    for transaction in transactions:
                        if set(c).issubset(set(transaction)):
                            count += 1

                        if set(c[1:]).issubset(set(transaction)):
                            tail_count += 1

                    if (count/len(transactions)) >= float(mis[c[0]]):
                        Fk.append(c)

                    tail_count_dict[''.join(c)] = tail_count


                if len(Fk) > 0:
                    #Fk = must_have_constraint(Fk)
                    #Fk = cannot_have_constraint(Fk)
                    F.append(Fk)


    # applying must have and cannot have constraints
    for i in range(0,len(F)):
        F[i] = must_have_constraint(F[i])
        F[i] = cannot_have_constraint(F[i])

    f = open(sys.argv[3],'w')
    for i in range(0,len(F)):

        if len(F[i]) == 0 and i is not 0:
            continue
        set1 = {}
        f.write("Frequent " + str(i+1) + "-itemsets\n")
        for item in F[i]:
            if isinstance(item, (list,)):
                set1 = set(item)
            else:
                set1 = {item}
                item = [item]
            f.write("      " + str(calc_count(set1, transactions))+ " : { " + ", ".join(x.replace("'","") for x in item) + " }\n")
            if i is not 0:
                f.write("Tail Count = " + str(tail_count_dict[''.join(item)])+"\n")

        f.write("     Total number of frequent "+str(i+1)+"-itemsets = " + str(len(F[i]))+"\n")
        f.write("\n")
    f.flush()
    f.close()
    return F[-1]

def main():
    input()
    ms_apriori()


if __name__ == '__main__':
    main()