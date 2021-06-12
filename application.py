import tkinter as tk
import math
import random

x_away = 2000
y_away = 2000


def get_color_by_state(state):
    if state == "inactive":
        return "#cfcfcf"
    elif state == "active":
        return "#a8ffaa"
    elif state == "left":
        return "#fffbb5"
    elif state == "right":
        return "#ffbaba"
    elif state == "middle":
        return "#ffd591"
    elif state == "border":
        return "#b5c1ff"


class SparseTable:
    def __init__(self, array):
        self.columns_number = len(array)
        self.rows_number = int(math.log2(self.columns_number)) + 1
        self.logs = self._calculate_logs()
        self.table = self._build_sparse_table(array)

    def get_shapes(self):
        return self.rows_number, self.columns_number

    def get_cell_value(self, row, column):
        return self.table[row][column]

    def get_log_by_length(self, section_length):
        return self.logs[section_length]

    def get_minimum(self, index1, index2):
        if index1 > index2:
            index1, index2 = index2, index1

        section_length = index2 - index1 + 1
        return min(self.table[self.logs[section_length]][index1],
                   self.table[self.logs[section_length]][index2 - (1 << self.logs[section_length]) + 1])

    def _calculate_logs(self):
        logs = [0, 0]
        for i in range(2, self.columns_number + 1):
            logs.append(logs[i // 2] + 1)
        return logs

    def _build_sparse_table(self, array):
        table = [[None for g in range(self.columns_number)] for i in range(self.rows_number)]

        for i in range(self.columns_number):
            table[0][i] = array[i]

        for row in range(1, self.rows_number):
            for column in range(self.columns_number):
                if column + (1 << row) > self.columns_number:
                    break

                table[row][column] = min(table[row - 1][column], table[row - 1][column + (1 << (row - 1))])

        return table


class NumberTile:
    def __init__(self, number, state="inactive"):
        self.number = number
        self.state = state

    def set_state(self, state_to_set):
        if state_to_set == "right" and self.state == "left":
            self.state = "middle"
        else:
            self.state = state_to_set

    def draw_on(self, surface, index, x, y, size):
        surface.create_rectangle(x, y, x + size, y + size, fill=get_color_by_state(self.state))

        text_x = x + (size - 10*len(str(self.number))) / 2
        index_x = x + (size - 7*len(str(index))) / 2

        surface.create_text(text_x, y + 0.5*size, anchor=tk.W, font="Arial 16", text=str(self.number))
        surface.create_text(index_x, size + 10, anchor=tk.W, font="Arial 12", text=str(index))


class ArrayCanvas(tk.Canvas):
    def __init__(self, parent, window, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)

        self.window = window

        #Устанавливаем скролл бар для верхней панели
        self.scroll_bar = tk.Scrollbar(parent, orient=tk.HORIZONTAL)
        self.scroll_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.scroll_bar.config(command=self.xview)
        self.config(xscrollcommand=self.scroll_bar.set)

        #Поле для ввода чисел
        self.entry = tk.Entry(self, width=3, bg="#bdbdbd", font="Arial 16", justify="center")
        self.entry.place(x=-100, y=10)

        # Отображаем верхнюю панель
        self.pack(side=tk.TOP, expand=True, fill=tk.BOTH)

        self.bind_widgets()

        self.index_for_input = None
        self.current_tile_index = None
        self.tiles = []
        self.tile_size = kwargs["height"] - 20
        self.last_x = 0

    def bind_widgets(self):
        self.entry.bind("<Return>", self.process_enter_button)
        self.scroll_bar.bind("<B1-Motion>", self.process_scroll_move)
        self.bind("<Motion>", self.process_motion)
        self.bind("<Button-1>", self.process_left_click)
        self.bind("<Button-3>", self.process_right_click)
        self.entry.bind("<Right>", self.process_right_arrow)
        self.entry.bind("<Left>", self.process_left_arrow)
        self.entry.bind("<Escape>", self.process_escape)

    def _get_index_by_coords(self, x):
        return int(x // self.tile_size + (self.scroll_bar.get()[0] * len(self.tiles)))

    def get_numbers_list(self):
        if len(self.tiles) == 0:
            return []

        return [tile.number for tile in self.tiles]

    def get_current_size(self):
        return len(self.tiles)

    def redraw_all_tiles(self):
        self.delete("all")
        for index, tile in enumerate(self.tiles):
            if index == self.current_tile_index:
                tile.draw_on(self, index, index * self.tile_size, 0, self.tile_size)
            else:
                tile.draw_on(self, index, index * self.tile_size, 0, self.tile_size)
        self.config(scrollregion=self.bbox("all"))

    def add_tile(self, number=0):
        self.tiles.append(NumberTile(number))
        self.tiles[-1].draw_on(self, len(self.tiles) - 1, self.last_x, 0, self.tile_size)
        self.addtag_all("all")
        self.last_x += self.tile_size
        self.config(scrollregion=self.bbox("all"))

        self.window.hide_sparse_table()
        self.redraw_all_tiles()

    def delete_tile(self, index):
        if self.index_for_input is not None:
            self.hide_element_entry()
        self.tiles.pop(index)
        self.last_x -= self.tile_size
        self.current_tile_index = None

        self.window.hide_sparse_table()
        self.redraw_all_tiles()

    def delete_all_tiles(self):
        tiles_number = self.get_current_size()
        for i in range(0, tiles_number):
            self.delete_tile(0)

    def show_element_entry(self, tile_index):
        if self.index_for_input is not None:
            self.hide_element_entry()
        self.index_for_input = tile_index
        self.entry.insert(0, str(self.tiles[tile_index].number))
        self.entry.place(x=(tile_index - self.scroll_bar.get()[0] * self.get_current_size())*self.tile_size + 8, y=13)

    def hide_element_entry(self):
        if self.index_for_input is None:
            return

        entry_value = self.entry.get()
        if entry_value != str(self.tiles[self.index_for_input].number) and entry_value != "":
            if self.window.in_step_building:
                self.entry.place(x=-100, y=0)
                self.entry.delete(0, tk.END)
                self.index_for_input = None
                return

            try:
                if "." in entry_value:
                    entry_value = float(entry_value)
                else:
                    entry_value = int(entry_value)
            except Exception:
                entry_value = 0
                self.window.show_error_label("Введенное значение не число!")

            self.tiles[self.index_for_input].number = entry_value
            self.redraw_all_tiles()
            self.window.hide_sparse_table()

        self.entry.place(x=-100, y=0)
        self.entry.delete(0, tk.END)
        self.index_for_input = None

    def highlight_tile(self, index, mode):
        self.tiles[index].set_state(mode)
        self.tiles[index].draw_on(self, index, index * self.tile_size, 0, self.tile_size)

    def unhighlight_tile(self, index):
        self.tiles[index].set_state("inactive")
        self.tiles[index].draw_on(self, index, index * self.tile_size, 0, self.tile_size)

    def highlight_section(self, start_index, length, mode):
        for i in range(length):
            if start_index + i < self.get_current_size():
                self.highlight_tile(start_index + i, mode)

    def unhighlite_all_tiles(self):
        self.highlight_section(0, len(self.tiles), "inactive")

    def change_current_element(self, new_index):
        if self.current_tile_index is not None and self.current_tile_index < self.get_current_size():
            self.unhighlight_tile(self.current_tile_index)

        if 0 <= new_index < self.get_current_size():
            self.current_tile_index = new_index
            self.highlight_tile(new_index, "active")

    def process_motion(self, event):
        if not self.window.can_use_canvases():
            return

        self.change_current_element(self._get_index_by_coords(event.x))

    def process_scroll_move(self, event):
        self.hide_element_entry()

    def process_escape(self, event):
        self.entry.place(x=-100, y=0)
        self.entry.delete(0, tk.END)
        self.index_for_input = None

    def process_right_arrow(self, event):
        if self.index_for_input is not None and self.index_for_input + 1 < self.get_current_size():
            self.show_element_entry(self.index_for_input + 1)
            self.change_current_element(self.index_for_input)

    def process_left_arrow(self, event):
        if self.index_for_input is not None and self.index_for_input - 1 >= 0:
            self.show_element_entry(self.index_for_input - 1)
            self.change_current_element(self.index_for_input)

    def process_enter_button(self, event):
        self.hide_element_entry()

    def process_left_click(self, event):
        if not self.window.can_use_canvases():
            return

        index_of_tile = self._get_index_by_coords(event.x)
        if index_of_tile < self.get_current_size():
            self.show_element_entry(index_of_tile)

    def process_right_click(self, event):
        if not self.window.can_use_canvases():
            return

        index_of_tile = self._get_index_by_coords(event.x)
        if index_of_tile < len(self.tiles):
            self.delete_tile(index_of_tile)
            self.redraw_all_tiles()
            self.window.hide_sparse_table()


class TableCell:
    def __init__(self, number, state="inactive"):
        self.number = number
        self.state = state

    def set_state(self, state_to_set):
        if self.state == "left" and state_to_set == "right":
            self.state = "middle"
        else:
            self.state = state_to_set

    def draw_on(self, surface, x, y, size):
        surface.create_rectangle(x, y, x + size, y + size, fill=get_color_by_state(self.state))

        text = str(self.number) if self.number is not None else ""
        text_x = x + (size - 8*len(str(self.number))) / 2
        surface.create_text(text_x, y + 0.5*size, anchor=tk.W, font="Arial 12", text=text)


class TableCanvas(tk.Canvas):
    def __init__(self, parent, window, max_width, max_height, **kwargs):
        tk.Canvas.__init__(self, parent, **kwargs)

        self.window = window

        #Настройка скролл баров и отображения таблицы
        self.horizontal_scroll = tk.Scrollbar(parent, orient=tk.HORIZONTAL)
        self.horizontal_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.horizontal_scroll.config(command=self.xview)

        self.vertical_scroll = tk.Scrollbar(parent, orient=tk.VERTICAL)
        self.vertical_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.vertical_scroll.config(command=self.yview)

        self.config(xscrollcommand=self.horizontal_scroll.set, yscrollcommand=self.vertical_scroll.set)
        self.pack(expand=True, fill=tk.BOTH)

        self.bind("<Motion>", self.process_motion)

        self.max_width = max_width
        self.max_height = max_height

        self.last_x = 0
        self.last_y = 0
        self.cell_size = 35

        self.current_row = None
        self.current_column = None

        self.table_cells = None
        self.sparse_table = None

    def fill_table(self, array):
        self.sparse_table = SparseTable(array)

        table_rows, table_cols = self.sparse_table.get_shapes()

        self.config(width=min(self.max_width, (table_cols + 1) * self.cell_size),
                    height=min(self.max_height, (table_rows + 1) * self.cell_size))

        self.table_cells = [[None for g in range(table_cols)] for i in range(table_rows)]

        for i in range(table_rows):
            for g in range(table_cols):
                self.table_cells[i][g] = TableCell(self.sparse_table.get_cell_value(i, g))

    def redraw_table(self):
        self.delete("all")

        if self.sparse_table is not None:
            rows, columns = self.sparse_table.get_shapes()
        else:
            rows = columns = 0

        self.last_x = self.cell_size
        self.last_y = 0

        for column in range(columns):
            TableCell(number=column, state="border").draw_on(surface=self, x=self.last_x, y=0, size=self.cell_size)
            self.last_x += self.cell_size

        self.last_x = 0
        self.last_y = self.cell_size

        for row in range(rows):
            TableCell(number=row, state="border").draw_on(surface=self, x=0, y=self.last_y, size=self.cell_size)
            self.last_y += self.cell_size

        self.last_x = self.cell_size
        self.last_y = self.cell_size

        for row in range(rows):
            for column in range(columns):
                self.table_cells[row][column].draw_on(surface=self, x=self.last_x, y=self.last_y, size=self.cell_size)
                self.last_x += self.cell_size
            self.last_x = self.cell_size
            self.last_y += self.cell_size

        self.config(scrollregion=self.bbox("all"))

    def get_rows_number(self):
        return len(self.table_cells)

    def get_columns_number(self):
        return len(self.table_cells[0])

    def process_motion(self, event):
        if not self.window.can_use_canvases():
            return

        if self.current_row is not None and self.current_column is not None:
            self.unhighlight_cell(self.current_row, self.current_column)

        self.current_row = self.current_column = None

        if self.cell_size < event.x < self.cell_size * (self.sparse_table.get_shapes()[1] + 1) - 1:
            if self.cell_size < event.y < self.cell_size * (self.sparse_table.get_shapes()[0] + 1) - 1:
                self.current_row = self._get_row_by_y(event.y)
                self.current_column = self._get_column_by_x(event.x)

                self.highlight_cell_with_parents(self.current_row, self.current_column)

        self.redraw_table()

    def highlight_cell(self, row, column, mode="active"):
        self.table_cells[row][column].set_state(mode)
        self.redraw_table()

    def highlight_cell_with_parents(self, row, column):
        self.table_cells[row][column].set_state("active")

        if row > 0 and self.sparse_table.get_shapes()[1] - (1 << row) >= column:
            self.table_cells[row - 1][column].set_state("left")
            self.table_cells[row - 1][column + (1 << (row - 1))].set_state("right")

        self.redraw_table()

    def unhighlight_cell(self, row, column):
        self.table_cells[row][column].set_state("inactive")

        if row > 0 and self.get_columns_number() - (1 << row) >= column:
            self.table_cells[row - 1][column].set_state("inactive")
            self.table_cells[row - 1][column + (1 << (row - 1))].set_state("inactive")

        self.redraw_table()

    def unhighligth_all_cells(self):
        for row in range(self.get_rows_number()):
            for column in range(self.get_columns_number()):
                self.table_cells[row][column].set_state("inactive")

        self.redraw_table()

    def initialize_step_building(self):
        self.current_row = 0
        self.current_column = -1
        rows_number, columns_number = self.sparse_table.get_shapes()
        for row in range(rows_number):
            for column in range(columns_number):
                self.table_cells[row][column].number = ""
        self.redraw_table()

    def perform_action(self):
        self.table_cells[self.current_row][self.current_column].number =\
            self.sparse_table.get_cell_value(self.current_row, self.current_column)

        left_child_start = None
        right_child_start = None

        if self.current_row == 0:
            message_to_return = f"Минимум на отрезке длинны 1 начиная с индекса {self.current_column} - это," \
                                f"конечно, {self.sparse_table.get_cell_value(self.current_row, self.current_column)}."
        elif self.sparse_table.get_shapes()[1] - (1 << self.current_row) < self.current_column:
            message_to_return = f"Так как отрезок длины {1 << self.current_row} начиная с индекса {self.current_column} " \
                                f"выходит за пределы исходного массива,\n то оставляем данную клетку пустой."
        else:
            left_child_start = self.current_column
            right_child_start = self.current_column + (1 << (self.current_row - 1))

            message_to_return = f"Покрываем отрезок длины {1 << self.current_row} начиная с индекса {self.current_column} " \
                                f"двумя отрезками длины {1 << (self.current_row - 1)}. \nПервый начинается с индекса " \
                                f"{left_child_start} и имеет минимум " \
                                f"{self.sparse_table.get_cell_value(self.current_row - 1, left_child_start)}, второй " \
                                f"начинается с индекса {right_child_start} и имеет минимум " \
                                f"{self.sparse_table.get_cell_value(self.current_row - 1, right_child_start)}.\n" \
                                f"Заносим меньший из минимумов в таблицу, т.е. {self.sparse_table.get_cell_value(self.current_row, self.current_column)}"

        self.highlight_cell_with_parents(self.current_row, self.current_column)
        self.redraw_table()

        return {"left_start": left_child_start,
                "right_start" : right_child_start,
                "parent_row": self.current_row - 1,
                "message": "ОПИСАНИЕ ШАГА\n" + message_to_return}

    def to_next_step(self):
        rows_number, columns_number = self.sparse_table.get_shapes()

        self.unhighlight_cell(self.current_row, self.current_column)

        self.current_column += 1
        if self.current_column == columns_number:
            self.current_row += 1
            self.current_column = 0

        return self.perform_action()

    def to_previous_step(self):
        rows_number, columns_number = self.sparse_table.get_shapes()

        self.table_cells[self.current_row][self.current_column].number = ""
        self.unhighlight_cell(self.current_row, self.current_column)

        self.current_column -= 1
        if self.current_column == -1:
            self.current_row -= 1
            self.current_column = columns_number - 1

        return self.perform_action()

    def _get_column_by_x(self, x_value):
        return math.floor(x_value / self.cell_size +
                          (self.horizontal_scroll.get()[0] * self.sparse_table.get_shapes()[1])) - 1

    def _get_row_by_y(self, y_value):
        return math.floor(y_value / self.cell_size +
                          (self.vertical_scroll.get()[0] * self.sparse_table.get_shapes()[0])) - 1


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.width = 850
        self.height = 740
        self.geometry(f"{self.width}x{self.height}")
        self.title("Sparse Table by Bogdan Tkachenko")

        self.in_showing_answer = False
        self.in_step_building = False
        self.table_cell_size = 35

        self.array_frame = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.array_canvas = ArrayCanvas(self.array_frame, self, bg="white", width=750, height=70,
                                        scrollregion=(0, 0, 750, 0))

        self.table_frame = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.table_canvas = TableCanvas(self.table_frame, self, bg="white", max_width=735, max_height=175)

        self.button_add_tile = tk.Button(self, text="Добавить элемент", bg="#bdffc0")
        self.button_build_table = tk.Button(self, text="Построить Sparse Table", bg="#b5c1ff")
        self.button_step_build_table = tk.Button(self, text="Построить пошагово", bg="#b5c1ff")
        self.button_next_step = tk.Button(self, text="След. шаг", bg="#a8ffaa")
        self.button_previous_step = tk.Button(self, text="Пред. шаг", bg="#ffb0b0")
        self.button_end_steps = tk.Button(self, text="Завершить", bg="#b5c1ff")
        self.button_find_minimum = tk.Button(self, text="Найти минимум", bg="#b5c1ff")
        self.button_show_description = tk.Button(self, text="Описание")

        self.button_sample1 = tk.Button(self, text="1")
        self.button_sample2 = tk.Button(self, text="2")
        self.button_sample3 = tk.Button(self, text="3")

        self.array_label = tk.Label(self, text="Исходный массив", font="Arial 16")
        self.table_label = tk.Label(self, text="Разреженная таблица", font="Arial 16")
        self.finding_label = tk.Label(self, text="Поиск минимума на отрезке", font="Arial 16")
        self.error_label = tk.Label(self, text="", font="Arial 16", fg="red")
        self.action_label = tk.Label(self, text="", font="Arial 12", bg="white", width=92)
        self.samples_label = tk.Label(self, text="Пресеты", font="Arial 12")

        self.from_label = tk.Label(self, text="Индекс начала", font="Arial 12")
        self.to_label = tk.Label(self, text="Индекс конца", font="Arial 12")

        self.from_entry = tk.Entry(self, width=3, font="Arial 12")
        self.to_entry = tk.Entry(self, width=3, font="Arial 12")

        self.bind_widgets()
        self.place_widgets()

        self.mainloop()

    def bind_widgets(self):
        self.button_show_description.bind("<Button-1>", lambda event: self.show_description_window())
        self.button_add_tile.bind("<Button-1>", lambda event: self.add_element_to_array())
        self.button_build_table.bind("<Button-1>", lambda event: self.build_table())
        self.button_step_build_table.bind("<Button-1>", lambda event: self.start_step_building())

        self.button_next_step.bind("<Button-1>", lambda event: self.next_step())
        self.button_previous_step.bind("<Button-1>", lambda event: self.previous_step())
        self.button_end_steps.bind("<Button-1>", lambda event: self.end_step_building())

        self.button_find_minimum.bind("<Button-1>", lambda event: self.find_minimum())
        self.button_sample1.bind("<Button-1>", lambda event: self.load_sample(int(event.widget["text"])))
        self.button_sample2.bind("<Button-1>", lambda event: self.load_sample(int(event.widget["text"])))
        self.button_sample3.bind("<Button-1>", lambda event: self.load_sample(int(event.widget["text"])))

    def place_widgets(self):
        self.button_show_description.place(x=30, y=10)
        self.array_frame.place(x=30, y=95)
        self.button_add_tile.place(x=220, y=65)
        self.button_build_table.place(x=645, y=65)
        self.array_label.place(x=30, y=60)

        self.samples_label.place(x=630, y=10)
        self.button_sample1.place(x=710, y=10)
        self.button_sample2.place(x=740, y=10)
        self.button_sample3.place(x=770, y=10)

    def load_sample(self, sample_index):
        if self.in_step_building or self.in_showing_answer:
            return

        self.array_canvas.delete_all_tiles()

        if sample_index == 1:
            self.add_element_to_array(4)
            self.add_element_to_array(1)
            self.add_element_to_array(10)
            self.add_element_to_array(7)
            self.add_element_to_array(3)
            self.add_element_to_array(7)
            self.add_element_to_array(5)
        elif sample_index == 2:
            self.add_element_to_array(100)
            self.add_element_to_array(-2)
            self.add_element_to_array(10)
            self.add_element_to_array(0)
            self.add_element_to_array(1.45)
            self.add_element_to_array(-14)
            self.add_element_to_array(69)
            self.add_element_to_array(95)
            self.add_element_to_array(-12)
            self.add_element_to_array(-0.3)
            self.add_element_to_array(4)
            self.add_element_to_array(4.6)
            self.add_element_to_array(54)
            self.add_element_to_array(-17)
            self.add_element_to_array(-81)
            self.add_element_to_array(310)
        elif sample_index == 3:
            array_size = random.randint(5, 30)
            for _ in range(array_size):
                self.add_element_to_array(random.randint(-100, 100))

    def show_description_window(self):
        new_window = tk.Toplevel(self)
        new_window.geometry("1030x350")
        new_window.title("Описание приложения")
        description_label = tk.Label(new_window, justify="left",
                                     text="""
                                     Данное приложение служит для нахождения минимального элемента в массиве чисел с помощью Sparse Table.
        
                                    Использование приложения можно разбить на следующие этапы:
                                     
                                    1. Заполнение исходного массива
                                        С помощью кнопки 'Добавить элемент' Вы можете добавить элемент (изначально равный 0) в массив. Для изменения его значение нажмите ЛКМ по нему, введите значение
                                        и нажмите Enter. Для удаления элемента из массива нажмите по нему ПКМ. По элементам можно перемещаться с помощью стрелок на клавиатуре,
                                        таким образом быстро заполняя элементы массива.
                                    
                                    2. Построение Sparse Table
                                        После заполнения массива, нажмите кнопку 'Построить Sparse Table' чтобы построить разреженную таблицу. После ее построения появится кнопка 'Построить пошагово',
                                        которая позволяет перейти в режим пошагового построения таблицы с объяснениями каждого шага. С помощью соответствующих кнопок можно переходить от шага к шагу,
                                        а также досрочно завершить построение.
                                    
                                    3. Найти минимальный элемент на отрезке
                                        После построения разреженной таблицы появятся соответствующие поля для ввода индексов начала и конца отрезка, минимум на котором нужно найти.
                                        после заполнения этих полей нажмите на кнопку 'Найти минимум', чтобы получить минимальный элемент на отрезке.
                                    
                                    Автор: Ткаченко Богдан
                                    """)
        description_label.place(x=-100, y=5)

    def can_use_canvases(self):
        return not self.in_step_building and not self.in_showing_answer

    def find_minimum(self):
        left_index = self.from_entry.get()
        right_index = self.to_entry.get()

        try:
            left_index = int(left_index)
            if left_index < 0:
                self.show_error_label("Индекс начала меньше 0!")
                return
            elif left_index >= self.table_canvas.get_columns_number():
                self.show_error_label("Индекс начала больше максимального индекса!")
                return
        except:
            self.show_error_label("Индекс начала не число!")
            return

        try:
            right_index = int(right_index)
            if right_index < 0:
                self.show_error_label("Индекс конца меньше 0!")
                return
            elif right_index >= self.table_canvas.get_columns_number():
                self.show_error_label("Индекс конца больше максимального индекса!")
                return
        except:
            self.show_error_label("Индекс конца не число!")
            return

        if left_index > right_index:
            self.show_error_label("Индекс начала больше чем индекс конца!")
            return

        answer = self.table_canvas.sparse_table.get_minimum(left_index, right_index)
        self.show_answer(left_index, right_index, answer)

    def build_table(self):
        if not self.can_use_canvases():
            return

        numbers_array = self.array_canvas.get_numbers_list()
        if len(numbers_array) > 1:
            self.table_canvas.fill_table(numbers_array)
            self.table_canvas.redraw_table()
            self.show_sparse_table()
            self.show_finding_block()
        else:
            self.show_error_label("Заполните массив как минимум 2 элементами")
            self.hide_sparse_table()

    def add_element_to_array(self, number=0):
        if not self.can_use_canvases():
            return

        self.hide_sparse_table()
        self.array_canvas.add_tile(number)

    def start_step_building(self):
        if not self.can_use_canvases():
            return
        self.in_step_building = True

        self.hide_finding_block()

        self.action_label["text"] = ""
        self.button_step_build_table["state"] = "disabled"
        self.button_build_table["state"] = "disabled"
        self.button_add_tile["state"] = "disabled"

        self.button_previous_step.place(x=self.table_frame.winfo_x() + self.table_frame.winfo_width() / 2 - 75,
                                        y=self.table_frame.winfo_y() + self.table_frame.winfo_height() + 8)

        self.button_next_step.place(x=self.table_frame.winfo_x() + self.table_frame.winfo_width() / 2 + 15,
                                    y=self.table_frame.winfo_y() + self.table_frame.winfo_height() + 8)

        self.button_end_steps.place(x=self.table_frame.winfo_x() + self.table_frame.winfo_width() / 2 + 100,
                                    y=self.table_frame.winfo_y() + self.table_frame.winfo_height() + 8)

        self.action_label.place(x=5, y=600)

        self.table_canvas.initialize_step_building()

    def end_step_building(self):
        self.in_step_building = False

        self.table_canvas.current_row = self.table_canvas.current_column = None
        self.build_table()
        self.table_canvas.redraw_table()

        self.array_canvas.highlight_section(0, self.table_canvas.get_columns_number(), "inactive")
        self.array_canvas.redraw_all_tiles()

        self.show_finding_block()

        self.button_step_build_table["state"] = "normal"
        self.button_build_table["state"] = "normal"
        self.button_add_tile["state"] = "normal"

        self.button_previous_step.place(x=x_away, y=y_away)
        self.button_next_step.place(x=x_away, y=y_away)
        self.button_end_steps.place(x=x_away, y=y_away)
        self.action_label.place(x=x_away, y=y_away)

        self.action_label["text"] = ""

    def next_step(self):
        table_rows, table_cols = self.table_canvas.sparse_table.get_shapes()
        if self.table_canvas.current_row == table_rows - 1 and self.table_canvas.current_column == table_cols - 1:
            self.end_step_building()
        else:
            step_log = self.table_canvas.to_next_step()
            self.action_label["text"] = step_log["message"]
            self.array_canvas.unhighlite_all_tiles()
            if step_log["left_start"] is not None and step_log["right_start"] is not None and step_log[
                "parent_row"] >= 0:
                self.array_canvas.highlight_section(step_log["left_start"], 1 << step_log["parent_row"], "left")
                self.array_canvas.highlight_section(step_log["right_start"], 1 << step_log["parent_row"], "right")

    def previous_step(self):
        if self.table_canvas.current_row == 0 and self.table_canvas.current_column <= 0:
            return
        else:
            step_log = self.table_canvas.to_previous_step()
            self.action_label["text"] = step_log["message"]
            self.array_canvas.unhighlite_all_tiles()
            if step_log["left_start"] is not None and step_log["right_start"] is not None and step_log[
                "parent_row"] >= 0:
                self.array_canvas.highlight_section(step_log["left_start"], 1 << step_log["parent_row"], "left")
                self.array_canvas.highlight_section(step_log["right_start"], 1 << step_log["parent_row"], "right")

    def show_finding_block(self):
        self.finding_label.place(x=30, y=470)
        self.from_label.place(x=230, y=530)
        self.to_label.place(x=460, y=530)
        self.from_entry.place(x=350, y=530)
        self.to_entry.place(x=570, y=530)
        self.button_find_minimum.place(x=360, y=570)

        self.to_entry["text"] = ""
        self.from_entry["text"] = ""

    def hide_finding_block(self):
        self.finding_label.place(x=x_away, y=y_away)
        self.to_label.place(x=x_away, y=y_away)
        self.from_label.place(x=x_away, y=y_away)
        self.to_entry.place(x=x_away, y=y_away)
        self.from_entry.place(x=x_away, y=y_away)
        self.button_find_minimum.place(x=x_away, y=y_away)

    def show_sparse_table(self):
        self.table_label.place(x=30, y=215)
        self.table_frame.place(x=30, y=255)
        self.button_step_build_table.place(x=260, y=215)

    def hide_sparse_table(self):
        self.table_label.place(x=x_away, y=y_away)
        self.table_frame.place(x=x_away, y=y_away)
        self.button_step_build_table.place(x=x_away, y=y_away)
        self.hide_finding_block()

    def show_answer(self, left_index, right_index, answer):
        self.in_showing_answer = True
        self.action_label.place(x=5, y=630)
        self.action_label["text"] = f"Ответ : минимум на отрезке [{left_index}; {right_index}] это {answer}"

        parent_row = self.table_canvas.sparse_table.get_log_by_length(right_index - left_index + 1)

        self.array_canvas.unhighlite_all_tiles()
        self.array_canvas.highlight_section(left_index, 1 << parent_row, "left")
        self.array_canvas.highlight_section(right_index - (1 << parent_row) + 1, 1 << parent_row, "right")

        self.table_canvas.unhighligth_all_cells()
        self.table_canvas.highlight_cell(parent_row, left_index, "left")
        self.table_canvas.highlight_cell(parent_row, right_index - (1 << parent_row) + 1, "right")

        self.after(6500, self.stop_showing_answer)

    def stop_showing_answer(self):
        self.in_showing_answer = False
        self.action_label.place(x=x_away, y=y_away)
        self.array_canvas.unhighlite_all_tiles()
        self.table_canvas.unhighligth_all_cells()

    def show_error_label(self, error_text):
        self.error_label["text"] = "Ошибка : " + error_text
        self.error_label.place(x=(self.width - len(self.error_label["text"]) * 11) / 2, y=700)
        self.after(4000, self.hide_error_label)

    def hide_error_label(self):
        self.error_label.place(x=x_away, y=y_away)


Application()
