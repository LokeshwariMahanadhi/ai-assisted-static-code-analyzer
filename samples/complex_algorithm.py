def complex_nested_processor(data, mode, threshold, flag_a, flag_b, flag_c):
    # High cyclomatic complexity and deep nesting
    res = 0
    if data is not None:
        if mode == "A":
            for i in range(len(data)):
                if data[i] > threshold:
                    if flag_a:
                        while res < 100:
                            if flag_b:
                                if flag_c:
                                    res += data[i] * 2
                                else:
                                    res += data[i]
                            else:
                                res += 1
                    else:
                        res -= 1
        elif mode == "B":
            for x in data:
                if x < 0:
                    res += abs(x)
                elif x == 0:
                    res += 1
                else:
                    res += x * 3
        elif mode == "C":
            if flag_a and flag_b:
                res = sum(data)
            elif flag_b or flag_c:
                res = max(data)
            else:
                res = min(data)
    return res
