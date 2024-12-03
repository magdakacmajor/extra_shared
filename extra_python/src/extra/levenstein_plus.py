import numpy
import javalang

def levenshtein(token1, token2):
    distances = numpy.zeros((len(token1) + 1, len(token2) + 1))

    for t1 in range(len(token1) + 1):
        distances[t1][0] = t1

    for t2 in range(len(token2) + 1):
        distances[0][t2] = t2
        
    a = 0
    b = 0
    c = 0
    
    for t1 in range(1, len(token1) + 1):
        for t2 in range(1, len(token2) + 1):
            if token1[t1-1] == token2[t2-1]:
                distances[t1][t2] = distances[t1 - 1][t2 - 1]
            else:
                a = distances[t1][t2 - 1]
                b = distances[t1 - 1][t2]
                c = distances[t1 - 1][t2 - 1]
                
                if (a <= b and a <= c):
                    distances[t1][t2] = a + 1
                elif (b <= a and b <= c):
                    distances[t1][t2] = b + 1
                else:
                    distances[t1][t2] = c + 1

    return int(distances[len(token1)][len(token2)])

def generated(ls):
    return [ls[1]] + ls [3:]

def target_len(tclines):
    return sum([ len(x.strip()) for x in generated(tclines)])

def process_single(path, num, opt, do_print=True):
#     path = '/klonhome/shared/data/apr_neweval/nowy-spsf/gen-for-hiprob02'
#     num=170
#     opt=0
    
    with open (f'{path}_fixed/{num}_{opt}.java') as f:
        fixed = f.read()
    with open (f'{path}/{num}_{opt}.java') as f:
#     with open (f'{path}_fixed_formatter_only/{num}_{opt}.java') as f:
        gen = f.read()
        
    with open (f'{path}_fixed/{num}_{opt}.java') as f:
        fixedlines = f.readlines()
    with open (f'{path}/{num}_{opt}.java') as f:
#     with open (f'{path}_fixed_formatter_only/{num}_{opt}.java') as f:
        genlines = f.readlines()
        
    gen_clean=' '.join([x.strip() for x in generated(genlines)])
    fixed_clean=' '.join([x.strip() for x in generated(fixedlines)])
    
    (leven, lengen, lenfixed) = levenshtein(gen_clean, fixed_clean), len(gen_clean), len(fixed_clean)

    slist_gen = list(javalang.tokenizer.tokenize(gen_clean))
    slist_fixed = list(javalang.tokenizer.tokenize(fixed_clean))
    plist_gen = [x.value for x in slist_gen]
    plist_fixed = [x.value for x in slist_fixed]

    (sleven, lengen_slist, lenfixed_slist) = levenshtein(plist_gen, plist_fixed), len(plist_gen), len(plist_fixed)
    
    if do_print:
        print('------')
        for x in plist_gen:
            print(x)
        print('------')
        for x in plist_fixed:
            print(x)

        print(f'{leven},{lengen},{lenfixed},{sleven},{lengen_slist},{lenfixed_slist}')
    
    return f'{num},{leven},{lengen},{lenfixed},{sleven},{lengen_slist},{lenfixed_slist}'
    
    
def process_list(path, list, opt):
    for num in list:
        print(process_single(path, num, opt, do_print=False))
        
    
def main():
    path = '/klonhome/shared/data/apr_neweval/nowy-spsf/gen-for-hiprob02/out'
    num=889
    opt=0
       
    process_single(path, num, opt)
    
    list1 = [1,5,8,9,11,15,17,18,20,22,24,29,31,32,33,37,42,43,45,48,51,53,54,55,56,62,64,65,66,68,70,75,
             76,78,79,81,84,87,88,91,92,93,94,97,98,102,104,105,107,110,111,114,117,119,120,122,125,128,
             133,134,136,139,145,147,148,149,150,152,153,154,157,160,161,163,164,165,170,173]
        
    list2 = [180,183,185,187,188,191,193,195,197,198,199,200,202,203,206,207,209,210,211,212,217,221,222,
              230,234,238,239,242,243,247,248,249,250,251,252,254,257,258,261,263,264,266,267,268,269,270,
              272,277,278,279,282,284,286,287,289,293,298,300,301,302,308,309,312,315,318,319,321,322,326,
              327,328,331,334,336,339,343,345,346,351,353,357,360,361,362,368,369,371,375,376,378,381,383,
              385,390,391,392,393,400,401,402,403,404,405,407,408,409,411,412,415,416,419,422,423,426,427,
              429,431,436,437,445,447,451,456,457,461,462,463,465,467,472,474,477,478,479,480,482]
    
    list3 = [484,488,493,495,499,500,501,502,503,504,507,508,509,510,516,519,520,528,533,534,540,542,543,545,
             551,552,554,555,556,558,559,566,571,572,573,576,578,580,583,584,586,591,594,596,597,598,600,606,
             608,611,614,615,616,617,621,622,626,627,628,631,634,636,637,640,641,642,643,644,648,650,651,655,656,
             658,664,669,670,671,672,675,676,677,681,684,686,687,691,692,694,697,698,699,700,702,705,707,708,
             709,710,713,714,716,717,724,726,727,728,730,732,741,742,744,745,746,748,750,755,759,761,762,763,
             765,766,769,770,773,776,777,780,786,787,790,792,793,795,796,797,800,802,803,808,810,814,815,818,
             819,825,826,832,833,834,837,839,840,842,843,845,852,853,854,857,859,861,865,866,869,872,882,883,
             884,886,887,890,891,892,893,898,902,907,908,909,910,914,915,917,918,919,920,922,923,924,926,927,
             930,933,935,937,939,940,945,946,948,952,954]
    
    l4=[103,146,373,505,562,633,673,738,798,822,876]
    
#     process_list(path, l4, opt)
    
if __name__ == '__main__':
    main()   