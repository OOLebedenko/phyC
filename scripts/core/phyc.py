import pandas as pd
from ete3 import Tree
from collections import defaultdict
from tqdm import tqdm


def _prepare_pos(info_pos):
    pos = [int(line.strip().split("\t")[0]) for line in open(info_pos)]
    SNPs = [line.strip().split("\t")[1] for line in open(info_pos)]
    ref = [line.strip().split("\t")[2] for line in open(info_pos)]
    return pos, SNPs, ref


def _prepare_structure(names_of_nodes, genotype, SNPs, ancestral=False):
    INFO_POS = defaultdict(lambda: defaultdict(list))
    for name in names_of_nodes:
        sequence = genotype[name]
        for ind in range(len(sequence)):
            if sequence[ind] == SNPs[ind]:
                if ancestral:
                    INFO_POS[ind][name].append(sequence[ind])
                else:
                    INFO_POS[ind][sequence[ind]].append(name)
    return INFO_POS


def traverse(leaves_INFO_POS, ancestral_INFO_POS, names_of_ancestral_R, tree, point, snp):
    R_list = []
    S_list = []
    for lleaf in leaves_INFO_POS[point][snp]:
        node = tree & lleaf
        ans_node = node.up
        while ancestral_INFO_POS[point][ans_node.name] == [snp]:
            node = ans_node
            ans_node = node.up
            if node.is_root():
                break
        if node.is_leaf():
            continue
        elif node.name in names_of_ancestral_R:
            R_list.append(node.name)
        else:
            S_list.append(node.name)
    resistant_branches = R_list
    sensitive_branches = S_list
    return resistant_branches, sensitive_branches


def phyc(name_of_R, name_of_S, names_of_ancestral_S, names_of_ancestral_R, info_pos, raxml_in, genotype):
    tree = Tree(raxml_in, format=1)
    names_of_ancestral = names_of_ancestral_R + names_of_ancestral_S
    pos, SNPs, ref = _prepare_pos(info_pos)
    R_INFO_POS = _prepare_structure(name_of_R, genotype, SNPs)
    S_INFO_POS = _prepare_structure(name_of_S, genotype, SNPs)
    ancestral_INFO_POS = _prepare_structure(names_of_ancestral, genotype, SNPs, ancestral=True)
    resistant_branches = []
    sensitive_branches = []
    for point, snp in tqdm(enumerate(SNPs), desc="phyc run, positions={iteration}".format(iteration = len(SNPs))):
        R1, S1 = traverse(R_INFO_POS, ancestral_INFO_POS, names_of_ancestral_R, tree, point, snp)
        R2, S2 = traverse(S_INFO_POS, ancestral_INFO_POS, names_of_ancestral_R, tree, point, snp)
        resistant_branches.append(len(set(R1 + R2)))
        sensitive_branches.append(len(set(S1 + S2)))
    R_S = pd.DataFrame({"pos": pos, "alt": SNPs, "ref": ref, "resistant": resistant_branches, "sensitive": sensitive_branches})
    return R_S
