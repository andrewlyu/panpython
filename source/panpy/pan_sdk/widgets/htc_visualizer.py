# https://gist.github.com/pbugnion/5bb7878ff212a0116f0f1fbc9f431a5c

import difflib
import ipywidgets as widgets
import pandas as pd
import seaborn as sn
from IPython.display import display
# from matplotlib.backends import backend_qt4agg
import numpy as np
import matplotlib.pyplot as plt


class PointHtcViz:
    def __init__(self, state_space, descriptions, table, units):
        self.state_space = state_space
        self.descriptions = descriptions
        self.table = table
        self.units = units

        # -- state space checkbox -- #
        # -- by default, T is not selected -- #
        self.state_space_dict = {
            state: widgets.Checkbox(description=state, value=(False if state == 'T' else True)) for state in state_space
        }
        self.state_options = [self.state_space_dict[state] for state in state_space]

        # -- property search box -- #
        self.search_prop_widget = widgets.Text(placeholder='phase name', description='Search:')

        # -- property option checkbox -- #
        # -- by default, nothing is selected -- #
        self.prop_options_dict = {
            description: widgets.Checkbox(description=description, value=False) for description in descriptions}
        self.prop_options = [self.prop_options_dict[description] for description in descriptions]

        # -- property range slider -- #
        self.prop_ranges_dict = {
            description: widgets.FloatRangeSlider(value=[table[description].min(), table[description].max()],
                                                  min=table[description].min(), max=table[description].max(),
                                                  step=(table[description].max() - table[description].min()) / 100.0,
                                                  description=description, layout=widgets.Layout(width='80%'),
                                                  style={'description_width': '30%'})
            for description in descriptions}
        # by default, no slider is displayed
        self.prop_ranges = []

        # -- the widget with state and property selectors -- #
        self.options_widget = widgets.HBox(
            [widgets.VBox([widgets.HTML(value="<b style=\"color:blue\">Select state</b>")] + self.state_options,
                          layout=widgets.Layout(width='40%', overflow='scroll')),
             widgets.VBox(
                 [widgets.HTML(value="<b style=\"color:blue\">Select properties</b>"),
                  self.search_prop_widget] + self.prop_options,
                 layout=widgets.Layout(width='60%', overflow='scroll'))],
            layout=widgets.Layout(width='100%')
        )

        # -- the widget with range slider -- #
        self.prop_ranges_widget = widgets.VBox(self.prop_ranges, layout={'overflow': 'scroll'})
        # multi_select = widgets.VBox([search_widget, options_widget])

        # -- the button to trigger displaying plot and table -- #
        self.button_box_plot = widgets.Button(description="Display/Refresh")

        # -- the widget to display table -- #
        self.out_df = widgets.Output()

        # -- the widget to display plot -- #
        self.out_box_plot = widgets.Output()
        self.out_corr = widgets.Output()
        self.prop_corr = widgets.Output()
        data1 = pd.DataFrame(np.random.normal(size=50))
        self.tab = widgets.Tab(children=[self.out_box_plot, self.out_corr, self.prop_corr])
        self.tab.set_title(0, 'State Dist.')
        self.tab.set_title(1, 'State/Prop. Corr.')
        self.tab.set_title(2, 'Prop. Corr.')

        # -- compile or widgets together for display -- #
        self.HTC_viz = widgets.VBox([self.options_widget, self.prop_ranges_widget,
                                     self.button_box_plot, self.tab, self.out_df])

    def run(self):
        self.search_prop_widget.observe(self.on_text_change, names='value')
        for key, op in self.prop_options_dict.items():
            op.observe(self.on_options_change, names='value')
        self.button_box_plot.on_click(self.on_click_box_plot_button)
        display(self.HTC_viz)

    # a function update output table
    def update_table(self):
        selected_phases = [w.description for w in self.prop_ranges_widget.children]
        m_filter = pd.Series(dtype=bool)
        for w in self.prop_ranges_widget.children:
            # print(w.description)
            val_max = w.value[1]
            val_min = w.value[0]
            # print('\t', val_max, val_min)
            if m_filter.empty:
                m_filter = (self.table[w.description] <= val_max) & (self.table[w.description] >= val_min)
            else:
                m_filter = m_filter & (self.table[w.description] <= val_max) & (self.table[w.description] >= val_min)
        m_copy_no_units = self.table.loc[m_filter].copy()
        m_copy = self.table.loc[m_filter].copy()
        m_copy.columns = pd.MultiIndex.from_arrays((['task_id'] + list(self.units.keys()), [''] + list(self.units.values())))
        m_copy.sort_values(by=selected_phases, ascending=False, inplace=True)

        # for state, w in state_space_dict.items():
        #     if not w.value:
        #         m_copy_no_units = m_copy_no_units.drop(state, axis=1)
        # print('table updated')
        return m_copy, m_copy_no_units

    # Wire the search field to the checkboxes
    def on_text_change(self, change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = [self.prop_options_dict[description] for description in self.descriptions]
        else:
            # Filter by search field using difflib.
            close_matches = difflib.get_close_matches(search_input, self.descriptions, cutoff=0.0)
            new_options = [self.prop_options_dict[description] for description in close_matches]
        self.options_widget.children = new_options

    # Wire the options to the range
    def on_options_change(self, change):
        check_input = change['new']
        if change['new'] != change['old']:
            # print(change['owner'].description, 'is changed')
            if not change['new']:
                new_ranges = [w for w in self.prop_ranges_widget.children
                              if w.description != change['owner'].description]
                # ranges_widget.children = new_ranges
            else:
                new_ranges = [w for w in self.prop_ranges_widget.children]
                new_ranges.append(self.prop_ranges_dict[change['owner'].description])
            self.prop_ranges_widget.children = new_ranges

    # Wire button click to box plot
    def on_click_box_plot_button(self, b):
        if len(self.prop_ranges_widget.children) == 0:
            with self.out_box_plot:
                self.out_box_plot.clear_output()
                print('Please select at least one property to visualize!!!')
            return
        df_copy, df_copy_no_units = self.update_table()

        box_index = []
        for index in self.state_space:
            if self.state_space_dict[index].value:
                box_index.append(index)
        prop_index = []
        for index, w in self.prop_options_dict.items():
            if w.value:
                prop_index.append(index)

        with self.out_box_plot:
            self.out_box_plot.clear_output()
            if not box_index:
                print('Please select at least one state (for example, composition or temperature) to plot!!!')
                return
            fig1, axes1 = plt.subplots()
            fig1.suptitle('Composition distribution', fontsize=14)
            # logo = plt.imread('resource/panpy-branding.png')
            # axes1.set_title('Composition distribution')
            # data1.hist(ax=axes1)
            df_copy_no_units.boxplot(box_index)
            plt.show()
            # fig = df_copy_no_units.boxplot(list(box_index)).get_figure()
            # fig.savefig('test.png')
        with self.out_corr:
            self.out_corr.clear_output()
            fig2, axes2 = plt.subplots()
            fig2.suptitle('State/Prop. Correlation', fontsize=14)
            corrMatrix = df_copy_no_units.corr()
            corrMatrix = corrMatrix[prop_index]
            # print(corrMatrix)
            corrMatrix = corrMatrix.loc[box_index]
            # print(corrMatrix)
            sn.heatmap(corrMatrix, cmap='jet', linewidths=.5, annot=True)
            plt.show()
        with self.prop_corr:
            self.prop_corr.clear_output()
            fig3, axes3 = plt.subplots()
            fig3.suptitle('Prop. Correlation', fontsize=14)
            corrMatrix = df_copy_no_units.corr()
            corrMatrix = corrMatrix[prop_index]
            corrMatrix = corrMatrix.loc[prop_index]
            sn.heatmap(corrMatrix, cmap='jet', linewidths=.5, annot=True)
            plt.show()
        with self.out_df:
            self.out_df.clear_output()
            display(df_copy)
