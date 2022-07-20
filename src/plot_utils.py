import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from powerlaw import ccdf


####
def plot_one_ccdf_per_istance(dict__instance__distribution, xaxis_label, title=None, cmap_name='hsv', show_legend=False, legend_title='', plot_zoom=False, xlims_zoom=None, ylims_zoom=None, figsize=(6 ,6)):

    list_instances = list(sorted(dict__instance__distribution.keys()))

    # a different color for each instance
    def get_cmap(n, name='hsv'):
        '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
        RGB color; the keyword argument name must be a standard mpl colormap name.'''
        return plt.cm.get_cmap(name, n)
    cmap = get_cmap(len(list_instances), cmap_name)

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    # inset axes...
    if plot_zoom:
        axins = ax.inset_axes([0.15, 0.1, 0.45, 0.45])

    for i, c_inst in enumerate(list_instances):

        c_distribution = dict__instance__distribution[c_inst]

        # using powerlaw package to compute the CCDF of the current distribution
        x, y = ccdf(c_distribution, linear_bins=False)

        # plotting
        ax.scatter(x, y, color=cmap(i), alpha=0.6, s=5, label=str(c_inst))

        if plot_zoom:
            axins.scatter(x, y, color=cmap(i), alpha=0.6, s=5, label=str(c_inst))

    ax.set_xlabel(xaxis_label, fontsize=21)
    ax.set_ylabel(r'CCDF: $P(X>x)$', fontsize=21)
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.tick_params(axis='x', which='minor', bottom=True)
    ax.tick_params(axis='both', which='major', labelsize=20)

    if title:
        ax.set_title(title, fontsize=22)
    ax.grid(alpha=0.2)

    if plot_zoom:
        rect = patches.Rectangle((xlims_zoom[0], ylims_zoom[0]),
                                 xlims_zoom[1 ] -xlims_zoom[0],
                                 ylims_zoom[1 ] -ylims_zoom[0],
                                 linewidth=2, ls='--', edgecolor='grey', facecolor='none')
        ax.add_patch(rect)
        axins.set_yscale('log')
        axins.set_xscale('log')
        axins.tick_params(axis='x', which='minor', bottom=True)
        axins.tick_params(axis='both', which='major', labelsize=15)
        if xlims_zoom != None and ylims_zoom != None:
            axins.set_xlim(xlims_zoom[0], xlims_zoom[1])
            axins.set_ylim(ylims_zoom[0], ylims_zoom[1])
        axins.grid(alpha=0.2)

    if show_legend:
        leg = ax.legend(fontsize=14, scatterpoints=5, markerscale=1.2, labelspacing=0.3,
                        title=legend_title, title_fontsize=16,
                        bbox_to_anchor=(1.02,0.85)
                        )
        leg._legend_box.align = "center"
        plt.setp(leg.get_title(), multialignment='center')

    plt.tight_layout()
    # plt.show()

    return fig, ax
####

####
def Lorenz(v, bins):
    total = float(np.sum(v))
    yvals = []
    for b in bins:
        bin_vals = v[v <= np.percentile(v, b)]
        bin_fraction = (np.sum(bin_vals) / total) * 100.0
        yvals.append(bin_fraction)
    # perfect equality area
    pe_area = np.trapz(bins, x=bins)
    # lorenz area
    lorenz_area = np.trapz(yvals, x=bins)
    gini_val = (pe_area - lorenz_area) / float(pe_area)
    return yvals, gini_val
####

####
def plot_errorbars(dict__xkey__distribution, plot_mean=True, x_label='', y_label='', cmap_name='coolwarm',
                   legend_loc='best', legend_title='', legend_cols=1, figsize=(6, 6)):
    """Plot one (or more) line(s) with errorbars (max 7) showing the mean or median of N distributions, one per instance, with the bars showing its standard deviation.

    Parameters:
    -----------
    dict__xkey__distribution : dict
        a dictionary with keys indicating the instances to which the distributions belong, and the distributios themselves as values.
        Note that the ordering of the points will follow the sorted list of the dictionary's keys.
        Also, the dict can contain other dicts. In this case, one line per dict is plotted.

    plot_mean : bool
        whether the points indicate the mean (if True) or the median (if False) of the distribution

    x_label : str
        the label for the x-axis

    y_label : str
        the label for the y-axis

    cmap_name : str
        name of matplotlib colormap

    legend_loc : str
        the location of the legend

    legend_title : str
        the legend title. Deafult: no title.

    legend_cols : int
        the number of columns in which to split the legend entries. Default is 1.

    figsize : tuple
        tuple indicating the width and height of the figure

    Returns:
    --------
    fig, ax : the resulting matplotlib Figure and Axis
    """

    ##
    def is_dict_of_dicts(dictionary):
        list_bool_dict = [1 if type(value) == dict else 0 for value in dictionary.values()]
        if sum(list_bool_dict) == len(dictionary.values()):
            return True
        else:
            return False

    ##
    def plot_one_line(dict__xkey__distribution, plot_mean, line_name='', line_color='#687cea', line_marker='o'):

        data = [distrib for x_key, distrib in sorted(dict__xkey__distribution.items())]
        list_of_x_keys = [x_key for x_key in sorted(dict__xkey__distribution.keys())]

        if plot_mean:
            line = np.array([np.nanmean(distrib) for distrib in data])
            # line_leg_label = 'avg'
        else:
            line = np.array([np.nanquantile(distrib, 0.5) for distrib in data])
            # line_leg_label = 'median'

        ax.errorbar(list_of_x_keys, line,
                    fmt=line_marker + '--', ms=7, elinewidth=2, capsize=5,
                    linewidth=1,
                    color=line_color, alpha=0.9,
                    label=line_name,
                    yerr=np.array([np.std(distrib) for distrib in data])
                    )

        return
    ##

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=figsize)

    if is_dict_of_dicts(dict__xkey__distribution):
        #
        def get_cmap(n, name='hsv'):
            '''Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
            RGB color; the keyword argument name must be a standard mpl colormap name.'''
            return plt.cm.get_cmap(name, n)

        #
        cmap = get_cmap(len(dict__xkey__distribution.keys()), cmap_name)
        list_markers = ['D', 'o', '^', 'v', 'X', 's', 'H']
        for i, (key, val) in enumerate(sorted(dict__xkey__distribution.items())):
            plot_one_line(val, plot_mean, line_name=key, line_color=cmap(i), line_marker=list_markers[i])
    else:
        plot_one_line(dict__xkey__distribution, plot_mean)

    ax.set_xlabel(x_label, fontsize=21)
    ax.set_ylabel(y_label, fontsize=21)
    ax.tick_params(axis='both', which='major', labelsize=18)
    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(alpha=0.2)

    ax.legend(fontsize=15, framealpha=0.7, markerscale=1,
              loc=legend_loc, title=legend_title, title_fontsize=16,
              handletextpad=0.4,
              ncol=legend_cols, columnspacing=0.8)

    plt.tight_layout()

    return fig, ax
####


def streetDraw(place, G, attribute_to_plot, normalize_by_length=False, show_legend=True, legend_title='', schemeColor='yelloworangered', reverse_schemeColor=False, scaleType = 'symlog', size=(600,600), save_fig=False):
    """ Plots a road network with the roads colored with respect to an attribute.

    Parameters
    ----------
    place : str
        the name of the place that is being plotted (only used for saving).

    G : networkx.MultiDiGraph
        the road network to be plotted.

    attribute_to_plot : str
        the name of the feature to be plotted. It must be present as an attribute of the graph's edges.
    
    normalize_by_length : boolean
        whether to normalize the value of the attribute with the edge's length.
    
    show_legend : boolean
        whether to show the legend (colorbar) or not.

    schemeColor : str
        the name of a Vega's color scheme (https://vega.github.io/vega/docs/schemes/)

    scaleType : str
        type of Vega scale for altair.Scale (continuous scales: 'linear', 'log', 'pow', 'sqrt', 'symlog', 'time', 'utc', 'sequential').
        More info here: https://vega.github.io/vega/docs/scales/

    size : tuple
        the size of the chart as (widthCanvas, heightCanvas).

    save_fig
        whether to save (in .svg and .png) the output chart or not.

    Returns
        the Altair chart.
    -------

    Credits to Daniele Fadda.
    
    
    """
    
    import osmnx as ox
    import pandas as pd
    import altair as alt
    from altair_saver import save
    alt.data_transformers.disable_max_rows()

    widthCanvas = size[0]
    heightCanvas = size[1]

    edges = ox.graph_to_gdfs(G, nodes=False, node_geometry=False)
    df = edges.reset_index()

    if attribute_to_plot:
        df.sort_values(by=attribute_to_plot, na_position='first', ascending=True, inplace=True)

        if normalize_by_length:
            attribute_to_plot_old = attribute_to_plot
            attribute_to_plot = attribute_to_plot + ' normalized'
            df[attribute_to_plot] = (df[attribute_to_plot_old]*10e-3) / df['length']
            if legend_title:
                plot_label = legend_title
            else:
                plot_label = '%s (grams per meter of road)' %attribute_to_plot_old
        else:
            if legend_title:
                plot_label = legend_title
            else:
                plot_label = '%s' %attribute_to_plot
        #
        first_nonzero = [x for x in abs(df[attribute_to_plot]).dropna().sort_values() if x != 0][0]
        #
        if show_legend:
            legend = alt.Legend(title=legend_title, 
                                #orient='bottom',
                                labelAlign='right',
                                labelFontSize=14,
                                #labelLimit=0,
                                titleFontSize=12,
                                gradientLength=300,
                                format='.2s')
        else:
            legend = None
        #
     
        lines = alt.Chart(df[df[attribute_to_plot]==0]).mark_geoshape(
            filled=False,
            strokeWidth=1.5,
            color='lightgray'
        )

        speedLines = alt.Chart(df[df[attribute_to_plot]!=0]).mark_geoshape(
            filled=False,
            strokeWidth=2.5
        ).encode(
            alt.Color(
                attribute_to_plot + ':Q',
                legend=legend,
                scale=alt.Scale(scheme=schemeColor, type=scaleType, constant=first_nonzero, reverse=reverse_schemeColor)
            )
        ).properties(
            width=widthCanvas,
            height=heightCanvas
        )

        chart = lines + speedLines
    
    else:
        lines = alt.Chart(df).mark_geoshape(
            filled=False,
            strokeWidth=1.5,
            color='gray'
        ).properties(
            width=widthCanvas,
            height=heightCanvas
        )
        chart = lines

    if save_fig:
        from altair_saver import save
        city = place.split(',')[0]
        attribute = attribute_to_plot.replace(' ', '_')
        save(chart, f'../results/imgs/{city}_map_{attribute}.png', scale_factor=2.0)
        #save(chart, f'{city}_map_{attribute}.svg')
        save(chart, f'../results/imgs/{city}_map_{attribute}.pdf')
        print(f'{city} images saved')

    return chart