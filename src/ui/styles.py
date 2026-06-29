def get_main_stylesheet(accent, main_bg, strong_line, faint_line, tabbar_bg, tab_inactive_bg, tab_active_bg, pane_bg, btn_ops_bg, btn_ops_hover_bg, btn_ops_hover_text, text_color, font_weight, bottom_bar_bg, main_bg_style):

    return f"""

        QWidget#CentralWidget {{ {main_bg_style} }}

        QTabWidget::pane {{ border-top: 2px solid {accent}; background: {pane_bg}; border-image:none; }}

        QTabBar {{ background-color: transparent; border: none; border-image:none; qproperty-drawBase: 0; }}

        QTabBar::tab {{ background: {tab_inactive_bg}; color: {text_color}; padding: 8px 24px 14px 24px; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 3px; margin-top: 6px; border: 1px solid rgba(0,0,0,0.15); border-bottom: none; font-family: 'Segoe UI'; font-weight: 500; font-size: 12px; border-image: none; }}

        QTabBar::tab:selected {{ background: {tab_active_bg}; color: {accent}; font-weight: bold; border: 1px solid {accent}; border-bottom: none; margin-top: 2px; padding-bottom: 16px; }}

        QTabBar::close-button {{ subcontrol-position: right; margin-bottom: 4px; }}

        QWidget#FavArea {{ border-image: none; background: transparent; }}

        QWidget#FavPanelWidget {{ background-color: {tab_active_bg}; border-bottom: {faint_line}; border-top: none; border-image: none; }}

        QWidget#HomeTab {{ border-image: none; background: transparent; }}

        QWidget#BottomBar {{ background-color: {bottom_bar_bg}; border-top: 2px solid {accent}; }}

        QPushButton#btn_ops,
        QPushButton#btn_config_menu {{

            background-color:
            {btn_ops_bg};

            border:
            1px solid #000000;

            color:
            {text_color};

            font-weight:
            {font_weight};

            border-radius:
            6px;

            font-size:
            14px;

            font-family:
            'Segoe UI';

            letter-spacing:
            1.5px;

            padding:
            3px;

        }}

        QPushButton#btn_ops:hover,
        QPushButton#btn_config_menu:hover {{

            background-color:
            {btn_ops_hover_bg};

            color:
            {btn_ops_hover_text};

            border:
            1px solid {accent};

            box-shadow:
            0px 0px 12px {accent};

        }}

        QPushButton#btn_save_session {{

            background-color:
            {btn_ops_bg};

            border:
            1px solid #000000;

            color:
            {text_color};

            border-radius:
            4px;

            font-family:
            'Segoe UI';

            font-weight:
            bold;

        }}

        QPushButton#btn_save_session:hover {{

            background-color:
            {accent};

            color:
            #07080a;

            border:
            1px solid #000000;

        }}

    """