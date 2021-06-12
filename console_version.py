import math
import random

def build_sparse_table(array):
    array_length = len(array)
    log_length = math.ceil(math.log(array_length, 2))

    sparse_table = [[math.inf for _ in range(log_length)] for _ in range(array_length)]

    for i in range(array_length):
        sparse_table[i][0] = array[i]

    for j in range(1, log_length):
        for i in range(array_length):
            if i + 2**(j-1) >= array_length:
                break
            sparse_table[i][j] = min(sparse_table[i][j-1], sparse_table[i + 2**(j-1)][j-1])

    return sparse_table

def get_min(sparse_table, l, r):
    if l == r:
        return sparse_table[l][0]

    k = math.ceil(math.log(r - l + 1, 2)) - 1
    return min(sparse_table[l][k], sparse_table[r - 2**k + 1][k])

print("Введите количество элементов массива: ", end="")
array_length = int(input())

print("\nВведите элементы массива: ")
array = []

for i in range(array_length):
    print(f"{i}: ", end="")
    array.append(int(input()))

sparse_table = build_sparse_table(array)
print("\nРазреженная таблица построена! Для того, чтобы завершить программу введите: -1 -1")

first_input = second_input = 0
while (True):
    print("\nВведите левую и правую границу запроса на минимум: ", end="")
    try:
        first_input, second_input = tuple(map(lambda x: int(x), input().split()))
    except ValueError:
        print("Ошибка! Были введены некорректные границы интервала!")
        continue

    if first_input == -1 and second_input == -1:
        break

    if not (0 <= first_input < len(array) and 0 <= second_input < len(array)):
        print("Ошибка! Границы интервала выходят за пределы массива!")
        continue

    print(f"Результат: минимум на отрезке [{first_input}, {second_input}] "
          f"это {get_min(sparse_table, first_input, second_input)}")

print("Завершение программы")
