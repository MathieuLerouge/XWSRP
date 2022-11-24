# Third-party libraries
import matplotlib.colors as predefined_colors


####################
# Global variables #
####################

UI_BODY_BACKGROUND_COLOR = '#111111'
UI_FONT_COLOR = '#f3f5f4'
# TODO remove if not necessary
# UI_top_banner_color = '#194572'
# UI_panel_banner_color = '#353535'
UI_PANEL_CONTENT_COLOR = '#252525'
UI_LINE_COLOR = '#4B5460'
UI_TABLE_STYLE_DATA = {'padding-left': '10px', 'border': f'1px solid {UI_LINE_COLOR}',
                       'backgroundColor': UI_BODY_BACKGROUND_COLOR, 'hover': 'transparent',
                       'color': UI_FONT_COLOR, 'textAlign': 'left', 'font-family': 'sans-serif', 'fontSize': 14}
UI_TABLE_STYLE_HEADER = {'padding-left': '10px', 'border': f'1px solid {UI_LINE_COLOR}',
                         'backgroundColor': UI_PANEL_CONTENT_COLOR,
                         'color': UI_FONT_COLOR, 'textAlign': 'left', 'font-family': 'sans-serif', 'fontSize': 14}
UI_CONFLICT_TASK_COLOR = predefined_colors.TABLEAU_COLORS['tab:red']
UI_CONFLICT_BOUND_COLOR = predefined_colors.CSS4_COLORS['firebrick']
