import matplotlib as mpl
import matplotlib.font_manager as fm
import seaborn as sns


TITLE_COLOR = '#212121'
AXIS_COLOR = '#757575'
GRID_COLOR = '#eeeeee'  # Previously lighter #f5f5f5.
DPI = 200

def set_plot_style():
    """ Set plot style.

    Args:
        None.

    Returns:
        Nothing. Sets style.
    """
    sns.set_style('white')
    
    # Set up Roboto. Must be downloaded in the current directory.
    # See https://stackoverflow.com/a/51844978/1840471.
    fm.fontManager.ttflist += fm.createFontList(['Roboto-Regular.ttf'])
    
    STYLE = {
        'savefig.dpi': DPI,
        'figure.dpi': DPI,
        'figure.figsize': (6.4, 4.8),  # Default.
        'font.sans-serif': 'Roboto',
        'font.family': 'sans-serif',
        # Set title text color to dark gray (https://material.io/color) not black.
        'text.color': TITLE_COLOR,
        # Axis titles and tick marks are medium gray.
        'axes.labelcolor': AXIS_COLOR,
        'xtick.color': AXIS_COLOR,
        'ytick.color': AXIS_COLOR,
        # Grid is light gray.
        'axes.grid' : True,
        'grid.color': GRID_COLOR,
        # Equivalent to seaborn.despine(left=True, bottom=True).
        'axes.spines.left': False,
        'axes.spines.right': False,
        'axes.spines.top': False,
        'axes.spines.bottom': False
    }
    
    mpl.rcParams.update(STYLE)
