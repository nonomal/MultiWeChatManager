import random
import tkinter as tk
from enum import Enum
from functools import partial
from tkinter import ttk

from public_class.enums import NotebookDirection
from utils import widget_utils
from utils.encoding_utils import ColorUtils
from utils.widget_utils import UnlimitedClickHandler, CanvasUtils, WidgetUtils


class CustomBtn(tk.Widget):
    _default_styles = {}
    _styles = {}
    _down = False
    _text = ""
    _click_map = {}
    _click_func = None
    _click_time = 0
    _shake_running = None
    _state = None
    _core_widget = None

    class State(str, Enum):
        NORMAL = "normal"
        DISABLED = "disabled"
        SELECTED = "selected"
        CLICKED = "clicked"
        HOVERED = "hovered"

    def _init_custom_btn_attrs(self):
        # print("加载CustomBtn类的属性...")
        self._default_styles = {}
        self._styles = {}
        self._down = False
        self._text = ""
        self._click_map = {}
        self._click_func = None
        self._click_time = 0
        self._shake_running = None
        self._state = None
        self._core_widget = None
        # 默认颜色
        default_major_bg_color = '#B2E0F7'  # 主后色: 淡蓝色
        default_major_fg_color = 'black'  # 主前色: 黑色
        default_bg = {
            self.State.NORMAL: "white",
            self.State.HOVERED: ColorUtils.fade_color(default_major_bg_color),
            self.State.CLICKED: default_major_bg_color,
            self.State.DISABLED: "#F9F9F9",
            self.State.SELECTED: default_major_bg_color
        }
        default_fg = {
            self.State.NORMAL: default_major_fg_color,
            self.State.HOVERED: default_major_fg_color,
            self.State.CLICKED: default_major_fg_color,
            self.State.DISABLED: "grey",
            self.State.SELECTED: default_major_fg_color
        }
        default_bdc = {
            self.State.NORMAL: "#D0D0D0",
            self.State.HOVERED: default_major_bg_color,
            self.State.CLICKED: ColorUtils.brighten_color(default_major_bg_color),
            self.State.DISABLED: "#E9E9E9",
            self.State.SELECTED: "grey"
        }
        for key in [self.State.NORMAL, self.State.HOVERED, self.State.CLICKED, self.State.DISABLED,
                    self.State.SELECTED]:
            self._default_styles[key] = {'bg': default_bg[key], 'fg': default_fg[key], 'bdc': default_bdc[key]}

    def set_bind_map(self, **kwargs):
        """传入格式: **{"数字": 回调函数, ...},添加后需要apply_bind()才能生效"""
        for key, value in kwargs.items():
            self._click_map[key] = value
        return self

    def set_bind_func(self, func):
        """传入带有click_time参数的方法,变量名必须是click_time"""
        self._click_func = func
        return self

    def apply_bind(self, tkinter_root):
        """可以多次应用,每次应用不覆盖之前绑定的事件,注意不要重复,最好是在所有set_bind之后才apply_bind"""
        UnlimitedClickHandler(
            tkinter_root,
            self._core_widget,
            self._click_func,
            **self._click_map
        )
        # 绑定后清空map和func
        self._click_map = {}
        self._click_func = None

    def reset_bind(self):
        WidgetUtils.unbind_all_events(self._core_widget)
        self._bind_event()

    def _bind_event(self):
        self._core_widget.bind("<Enter>", self._on_enter)
        self._core_widget.bind("<Leave>", self._on_leave)
        self._core_widget.bind("<Button-1>", self._on_button_down)
        self._core_widget.bind("<ButtonRelease-1>", self._on_button_up)
        self._core_widget.bind("<Configure>", lambda e: self._draw())
        # self._draw()

    def redraw(self):
        """应用并重绘,前面可以链式修改"""
        self._draw()

    def set_state(self, state):
        """设置状态"""
        if not isinstance(state, self.State):
            raise ValueError("state必须是CustomLabelBtn.State的枚举值")
        self._state = state
        self._draw()

    def set_major_colors(self, major_color):
        """设置主要颜色（选中背景色和悬浮背景色）"""
        lighten_color = ColorUtils.fade_color(major_color)
        brighten_color = ColorUtils.brighten_color(major_color)
        self._styles[self.State.HOVERED]['bg'] = lighten_color
        self._styles[self.State.SELECTED]['bg'] = major_color
        self._styles[self.State.CLICKED]['bg'] = major_color
        self._styles[self.State.HOVERED]['bdc'] = major_color
        self._styles[self.State.CLICKED]['bdc'] = brighten_color
        self._styles[self.State.SELECTED]['bdc'] = brighten_color
        return self

    def set_styles(self, styles):
        """
        批量更新样式配置
        参数:
            styles (dict): 传入一个字典，格式例如：
                {
                    'disabled': {'fg': 'red'},
                    'selected': {'bg': '#00FF00', 'fg': 'white'},
                }
        说明：
            - 字典的键是状态名（'disabled', 'selected', 'hovered', 'normal'）
            - 每个值是一个dict，里面是Tkinter支持的样式参数（如'bg', 'fg'等）
            - 只修改指定的部分，不影响其他已有配置
        """
        if not isinstance(styles, dict):
            raise ValueError("styles必须是字典")
        for key, value in styles.items():
            if key not in self.State._value2member_map_:
                print(f"[Warning] 未知的状态名: '{key}'，跳过。必须是 {list(self.State._value2member_map_.keys())}")
                continue
            if not isinstance(value, dict):
                print(f"[Warning] 状态 '{key}' 的样式必须是字典，但收到的是 {type(value).__name__}，跳过。")
                continue
            if key not in self._styles:
                self._styles[key] = {}
            self._styles[key].update(value)

        return self

    def _draw(self):
        ...

    @staticmethod
    def set_all_custom_widgets_to_(frame, state: State):
        """
        将指定框架内所有继承自 CustomWidget 的控件设置为指定状态（递归子控件）

        :param frame: 要处理的 Frame 或控件容器
        :param state: CustomWidget.State 中的状态值
        """
        for child in frame.winfo_children():
            if isinstance(child, CustomBtn):
                child.set_state(state)
            # 如果子控件也是容器（比如 Frame），递归处理
            if isinstance(child, (tk.Frame, ttk.Frame)):
                CustomBtn.set_all_custom_widgets_to_(child, state)

    def _set_click_time(self, click_time):
        self._click_time = click_time

    def set_text(self, new_text):
        """用不同底层实现,设置文本的方式不同,需要重写"""
        self._text = new_text
        return self

    def _on_enter(self, event=None):
        if event:
            pass
        if self._state in [self.State.DISABLED, self.State.SELECTED]:
            return
        if self._down:
            self.set_state(self.State.CLICKED)
        else:
            self.set_state(self.State.HOVERED)

    def _on_leave(self, event=None):
        if event:
            pass
        if self._state in [self.State.DISABLED, self.State.SELECTED]:
            return
        self.set_state(self.State.NORMAL)

    def _on_button_down(self, event=None):
        self._down = True
        # print("定制按钮监听:按下")
        if event:
            pass
        if self._state == self.State.DISABLED:
            self._shake()
            return
        if self._state == self.State.SELECTED:
            return
        # 按下是短暂的选中状态
        self.set_state(self.State.CLICKED)

    def _on_button_up(self, event=None):
        self._down = False
        # print("定制按钮监听:抬起")
        if event:
            pass
        if self._state == self.State.DISABLED or self._state == self.State.SELECTED:
            return
        # 按下鼠标后，当抬起时位置不在按钮处，应该取消点击的状态
        x, y = self.winfo_pointerxy()
        widget = self.winfo_containing(x, y)
        # Printer().debug(f"触发的控件是: {self._core_widget}")
        # Printer().debug(f"停留的控件是: {widget}")
        if widget is not self._core_widget:
            self.set_state(self.State.NORMAL)
            return
        self.set_state(self.State.HOVERED)

    def _shake(self):
        """禁用状态下点击，抖动一下提示，不破坏布局"""
        if self._shake_running:
            return
        self._shake_running = True

        if self.winfo_manager() != 'pack':
            return

        info = self.pack_info()
        original_padx = info.get('padx', 0)
        dx = [2, -2, 2, -2, 0]

        def move(index=0):
            if index < len(dx):
                new_padx = max(0, original_padx + dx[index])
                self.pack_configure(padx=new_padx)
                self.after(30, move, index + 1)
            else:
                self.pack_configure(padx=original_padx)
                self._shake_running = False

        move()


class CustomCornerBtn(tk.Frame, CustomBtn):
    """
    基于Frame+Canvas的定制按钮,可以设定宽高,圆角,边框,边距等属性.
    当传入边距时,会根据文本内容自动调整大小以适应边距.
    """

    def __init__(self, parent, text="Button", corner_radius=4, width=100, height=30,
                 border_color='#D0D0D0', border_width=1, i_padx=None, i_pady=None, *args, **kwargs):
        super().__init__(parent, width=width, height=height, *args, **kwargs)
        self._init_custom_btn_attrs()
        self._text = text
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.border_color = border_color
        self.border_width = border_width
        self.i_padx = i_padx
        self.i_pady = i_pady

        # 内部 Canvas
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self._core_widget = self.canvas
        self._core_widget.pack(fill="both", expand=True)

        self.set_styles(self._default_styles)
        self.pack_propagate(False)  # 禁止根据子组件改变大小,因为Canvas依赖Frame大小,自适应会导致无限循环
        self.grid_propagate(False)  # 禁止根据子组件改变大小
        self.set_state(self.State.NORMAL)
        self._bind_event()

    def _draw(self):
        """根据当前状态重绘按钮"""
        self.canvas.delete("all")
        w, h, tx, ty = self._auto_resize_by_text()
        r = min(self.corner_radius, h // 2, w // 2)
        bg = self._styles[self._state]['bg']
        fg = self._styles[self._state]['fg']
        bdc = self._styles[self._state]['bdc']

        CanvasUtils.draw_rounded_rect(
            canvas=self.canvas,
            x1=0, y1=0, x2=w, y2=h,
            radius=r,
            border_width=self.border_width,
            bg_color=bg,
            border_color=bdc
        )
        # 居中文本
        self.text_id = self.canvas.create_text(tx, ty, text=self._text, fill=fg)

    def _auto_resize_by_text(self):
        """如果有边距,会根据文本内容自动调整大小以适应边距"""

        def _try_unpack(v):
            try:
                a, b = v
                return int(a), int(b)
            except TypeError:
                try:
                    a = b = int(v) if v is not None else 0
                except TypeError:
                    a = b = 0
            return a, b

        # 用系统默认字体
        import tkinter.font
        font = tkinter.font.nametofont("TkDefaultFont")
        line_height = font.metrics("linespace")
        lines = self._text.split('\n')
        # 计算新的宽高
        pl, pr = _try_unpack(self.i_padx)
        if self.i_padx is not None:
            text_width = max(font.measure(line) for line in lines)
            w = text_width + pl + pr
            self.config(width=w)
        else:
            w = self.winfo_width()
        pt, pb = _try_unpack(self.i_pady)
        if self.i_pady is not None:
            text_height = len(lines) * line_height
            h = text_height + pt + pb
            self.config(height=h)
        else:
            h = self.winfo_height()
        # 计算文本居中锚点
        tx = (w + pl - pr) // 2
        ty = (h + pb - pt) // 2
        # print(w, h, tx, ty)
        return w, h, tx, ty

    def set_corner_radius(self, radius):
        """
        设置固定圆角半径，然后立即重绘
        """
        self.corner_radius = radius
        return self

    def set_corner_scale(self, scale):
        """
        根据比例设置圆角，比例是相对于短边的（宽和高中更小的那个边）
        比如 scale=0.2 表示短边的 20%
        """
        short_edge = min(self.winfo_width(), self.winfo_height())
        radius = int(short_edge * scale)
        self.corner_radius = radius
        return self

    def set_border(self, width, color):
        """设置边框宽度和边框主颜色,若之后重新设置主颜色,边框颜色会被覆盖"""
        self.border_width = width
        brighten_color = ColorUtils.brighten_color(color)
        self._styles[self.State.HOVERED]['bdc'] = color
        self._styles[self.State.CLICKED]['bdc'] = brighten_color
        self._styles[self.State.SELECTED]['bdc'] = brighten_color
        return self

    def set_propagate(self, propagate: bool):
        """设置是否允许子组件改变大小"""
        self.pack_propagate(propagate)
        self.grid_propagate(propagate)
        return self


class CustomLabelBtn(tk.Label, CustomBtn):
    def __init__(self, parent, text, *args, **kwargs):
        self._init_custom_btn_attrs()
        super().__init__(parent, text=text, relief='flat', *args, **kwargs)
        self._text = text
        self.bind('<Enter>', self._on_enter, add='+')
        self.bind('<Leave>', self._on_leave, add='+')
        self.bind('<Button-1>', self._on_button_down, add='+')
        self.bind('<ButtonRelease-1>', self._on_button_up, add='+')
        self._core_widget = self

        self.set_styles(self._default_styles)
        self.set_state(self.State.NORMAL)

    def _draw(self):
        """根据当前状态更新样式"""
        self.configure(bg=self._styles[self._state]['bg'], fg=self._styles[self._state]['fg'])
        self.config(text=self._text)


class CustomNotebook:
    def __init__(self, root, parent_frame, direction: NotebookDirection = NotebookDirection.TOP, *args, **kwargs):
        self.click_time = 0
        self.direction = direction
        self.root = root
        self.tabs = {}
        self.curr_tab_id = None
        self.selected_bg = '#00FF00'  # 默认选中颜色
        self.select_callback = None  # 选中回调函数

        self.notebook_frame = ttk.Frame(parent_frame, *args, **kwargs)
        self._pack_frame()
        self._create_containers()

    def _pack_frame(self):
        direction = self.direction
        if direction == NotebookDirection.TOP:
            self.notebook_frame.pack(fill='both', expand=True, side='top')
        elif direction == NotebookDirection.BOTTOM:
            self.notebook_frame.pack(fill='both', expand=True, side='bottom')
        elif direction == NotebookDirection.LEFT:
            self.notebook_frame.pack(fill='both', expand=True, side='left')
        elif direction == NotebookDirection.RIGHT:
            self.notebook_frame.pack(fill='both', expand=True, side='right')

    def _create_containers(self):
        """创建标签页和内容容器"""
        # 根据方向创建容器
        if self.direction in [NotebookDirection.TOP, NotebookDirection.BOTTOM]:
            # 水平布局
            self.tabs_frame = ttk.Frame(self.notebook_frame)
            self.frames_pool = ttk.Frame(self.notebook_frame)

            # 根据方向设置pack顺序
            if self.direction == NotebookDirection.TOP:
                self.tabs_frame.pack(side='top', fill='x')
                self.frames_pool.pack(side='top', fill='both', expand=True)
            else:
                self.frames_pool.pack(side='top', fill='both', expand=True)
                self.tabs_frame.pack(side='top', fill='x')

        else:
            # 垂直布局
            self.tabs_frame = ttk.Frame(self.notebook_frame)
            self.frames_pool = ttk.Frame(self.notebook_frame)

            # 根据方向设置pack顺序
            if self.direction == NotebookDirection.LEFT:
                self.tabs_frame.pack(side='left', fill='y')
                self.frames_pool.pack(side='left', fill='both', expand=True)
            else:
                self.frames_pool.pack(side='left', fill='both', expand=True)
                self.tabs_frame.pack(side='left', fill='y')

    def set_major_color(self, selected_bg='#00FF00'):
        """
        设置标签页的颜色
        :param selected_bg: 选中状态的背景色
        """
        self.selected_bg = selected_bg
        # 更新所有标签的颜色
        for tab_info in self.tabs.values():
            label = tab_info['label']
            label.set_major_colors(selected_bg)

    def add(self, tab_id, text, frame):
        """
        添加新的标签页
        :param tab_id: 标签页标识
        :param text: 标签页文本
        :param frame: 标签页内容框架
        """
        # 创建标签页
        print(f"添加标签页：{tab_id}")
        widget_frame = ttk.Frame(self.tabs_frame, relief="solid")
        now_index = len(self.tabs)  # 现有的标签数量刚好是新标签的索引
        w = 1
        h = 25
        if self.direction not in [NotebookDirection.LEFT, NotebookDirection.RIGHT]:
            widget_frame.grid(row=0, column=now_index, sticky="nsew", padx=2, pady=2)
            self.tabs_frame.grid_columnconfigure(now_index, weight=1)
            display_text = text
            tab_widget = CustomCornerBtn(
                widget_frame, text=display_text, width=w, height=h,
                corner_radius=0, border_width=0)
        else:
            widget_frame.grid(row=now_index, column=0, sticky="nsew", padx=2, pady=2)
            self.tabs_frame.grid_rowconfigure(now_index, weight=1)
            display_text = '\n'.join(text)
            tab_widget = CustomCornerBtn(
                widget_frame, text=display_text, width=h, height=w,
                corner_radius=0, border_width=0)

        tab_widget.pack(fill="both", expand=True)

        # 内部默认绑定事件: 记录点击次数, 点击大于一次时候切换标签页
        (tab_widget
         .set_bind_map(**{"1": partial(self.select, tab_id), })
         .set_bind_func(self._set_click_time)
         .apply_bind(self.root))

        # 存储标签页信息
        self.tabs[tab_id] = {
            'text': text,
            'tab_widget': tab_widget,
            'frame': frame,
            'widget_frame': widget_frame,
            'index': now_index
        }

    def _set_click_time(self, click_time):
        self.click_time = click_time

    def all_set_bind_map(self, **kwargs):
        """
        传入格式: **{"数字": 回调函数,...},添加后需要apply_bind()才能生效
        注意:为!!当前!!所有标签添加事件,后添加的标签页不会生效.
        """
        for tab_id, tab_info in self.tabs.items():
            tab_label = tab_info["tab_widget"]
            tab_label.set_bind_map(**kwargs)
        return self

    def all_set_bind_func(self, func):
        """
        传入带有click_time参数的方法,变量名必须是click_time
        注意:为!!当前!!所有标签添加事件,后添加的标签页不会生效.
        """
        for tab_id, tab_info in self.tabs.items():
            tab_label = tab_info["tab_widget"]
            tab_label.set_bind_func(func)
        return self

    def all_apply_bind(self, event):
        """
        可以多次应用,每次应用不覆盖之前绑定的事件,注意不要重复,最好是在所有set_bind之后才apply_bind
        注意:为!!当前!!所有标签添加事件,后添加的标签页不会生效.
        """
        for tab_id, tab_info in self.tabs.items():
            tab_label = tab_info["tab_widget"]
            tab_label.apply_bind(event)

    def select(self, tab_id):
        """
        选择指定的标签页
        :param tab_id: 标签页文本
        """
        print(f"选择标签页：{tab_id}")
        # 取消当前标签页的选中状态
        if self.curr_tab_id:
            self.tabs[self.curr_tab_id]["tab_widget"].set_state(CustomBtn.State.NORMAL)
            if self.direction in [NotebookDirection.TOP, NotebookDirection.BOTTOM]:
                self.tabs_frame.grid_columnconfigure(self.tabs[self.curr_tab_id]['index'], weight=1)
            elif self.direction in [NotebookDirection.LEFT, NotebookDirection.RIGHT]:
                self.tabs_frame.grid_rowconfigure(self.tabs[self.curr_tab_id]['index'], weight=1)

        # 设置新标签页的选中状态
        self.tabs[tab_id]["tab_widget"].set_state(CustomBtn.State.SELECTED)
        self.curr_tab_id = tab_id

        # 生成一个3-4的随机数
        random_num = random.randint(3, 5)

        if self.direction in [NotebookDirection.TOP, NotebookDirection.BOTTOM]:
            self.tabs_frame.grid_columnconfigure(self.tabs[self.curr_tab_id]['index'], weight=random_num)
        elif self.direction in [NotebookDirection.LEFT, NotebookDirection.RIGHT]:
            self.tabs_frame.grid_rowconfigure(self.tabs[self.curr_tab_id]['index'], weight=random_num)

        # 显示对应的内容
        for tab_text, tab_info in self.tabs.items():
            if tab_text == tab_id:
                tab_info['frame'].pack(fill='both', expand=True)
            else:
                tab_info['frame'].pack_forget()

        if callable(self.select_callback):
            self.select_callback(self.click_time)


if __name__ == '__main__':
    tk_root = tk.Tk()
    tk_root.geometry("400x300")


    def printer(click_time):
        print("按钮功能:连点次数为", click_time)


    # 创建竖向Notebook（左侧）
    my_nb_cls = CustomNotebook(tk_root, tk_root, direction=NotebookDirection.LEFT)

    # 创建横向Notebook（顶部）
    # my_nb_cls = CustomNotebook(tk_root, tk_root, direction=NotebookDirection.TOP)

    # 设置颜色（使用正绿色）
    my_nb_cls.set_major_color(selected_bg='#00FF00')

    nb_frm_pools = my_nb_cls.frames_pool

    # 创建标签页
    frame1 = ttk.Frame(nb_frm_pools)
    frame2 = ttk.Frame(nb_frm_pools)
    frame3 = ttk.Frame(nb_frm_pools)
    frame4 = ttk.Frame(nb_frm_pools)

    # 在标签页1中添加CustomLabelBtn
    btn1 = CustomCornerBtn(frame1, text="标签按钮1")
    # btn1.on_click(lambda: print("按钮1被点击"))
    btn1.pack(pady=10)
    widget_utils.UnlimitedClickHandler(
        tk_root, btn1,
        printer
    )
    btn2 = CustomLabelBtn(frame1, text="标签按钮2")
    # btn2.on_click(lambda: print("按钮2被点击"))
    btn2.pack(pady=10)

    # 在标签页2中添加CustomLabelBtn和标签
    ttk.Label(frame2, text="这是标签页2").pack(pady=10)
    btn3 = CustomLabelBtn(frame2, text="标签按钮3")
    # btn3.on_click(lambda: print("按钮3被点击"))
    btn3.pack(pady=10)

    # 在标签页3中添加CustomLabelBtn组
    btn_frame = ttk.Frame(frame3)
    btn_frame.pack(pady=20)
    btn4 = CustomLabelBtn(btn_frame, text="标签按钮4")
    # btn4.on_click(lambda: print("按钮4被点击"))
    btn4.pack(side='left', padx=5)
    btn5 = CustomLabelBtn(btn_frame, text="标签按钮5")
    # btn5.on_click(lambda: print("按钮5被点击"))
    btn5.pack(side='left', padx=5)

    # 添加标签页
    my_nb_cls.add("tab1", "标签1", frame1)
    my_nb_cls.add("tab2", "标签2", frame2)
    my_nb_cls.add("tab3", "标签3", frame3)
    my_nb_cls.all_set_bind_func(printer).all_apply_bind(tk_root)

    my_nb_cls.add("tab4", "标签4", frame4)

    btn = CustomCornerBtn(frame1, text="MI", corner_radius=100, width=300, height=300)
    btn.set_major_colors("#ffc500").redraw()
    btn.pack(padx=20, pady=20)
    print(btn.__dict__)

    tk_root.mainloop()
