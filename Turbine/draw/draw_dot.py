import pydot
from Tools.graph_mod.csdf_to_sdf import get_csdf_into_sdf
from Turbine.file_parser.turbine_parser import read_tur_file


class Dot(object):
    def __init__(self, dataflow):
        self._dotGraph = None
        self.dataflow = dataflow
        self._create_dot()

    def _create_dot(self):
        if self._dotGraph is None:
            self._dotGraph = pydot.Dot(graph_type='digraph', splines="spline", name=self.dataflow.name)
            for arc in self.dataflow.get_arc_list():
                m0 = self.dataflow.get_initial_marking(arc)
                ename = self.dataflow.get_arc_name(arc)
                buf = "{}={}".format(ename, m0)

                prod = self.dataflow.get_task_name(arc[0])
                cons = self.dataflow.get_task_name(arc[1])

                if self.dataflow.is_sdf:
                    task_duration_s = self.dataflow.get_task_duration(arc[0])
                    task_duration_t = self.dataflow.get_task_duration(arc[1])
                if self.dataflow.is_csdf:
                    task_duration_s = self.dataflow.get_phase_duration_list(arc[0])
                    task_duration_t = self.dataflow.get_phase_duration_list(arc[1])

                dot_prod = pydot.Node(prod+str(task_duration_s), style="bold", color="Blue")
                self._dotGraph.add_node(dot_prod)
                dot_cons = pydot.Node(cons+str(task_duration_t), style="bold", color="Blue")
                self._dotGraph.add_node(dot_cons)
                dot_buf = pydot.Node(buf, fontcolor="Red", shape="box", sides=4, color="Red")
                self._dotGraph.add_node(dot_buf)

                if self.dataflow.is_sdf:
                    self._dotGraph.add_edge(pydot.Edge(dot_prod, dot_buf, headlabel=self.dataflow.get_prod_rate(arc)))
                    self._dotGraph.add_edge(pydot.Edge(dot_buf, dot_cons, headlabel=self.dataflow.get_cons_rate(arc)))
                if self.dataflow.is_csdf:
                    self._dotGraph.add_edge(
                        pydot.Edge(dot_prod, dot_buf, headlabel=str(self.dataflow.get_prod_rate_list(arc))))
                    self._dotGraph.add_edge(
                        pydot.Edge(dot_buf, dot_cons, headlabel=str(self.dataflow.get_cons_rate_list(arc))))

    def write_dot(self, name=None):
        if name is None:
            name = self.dataflow.name
        self._dotGraph.write_dot(name + '.dot')

    def write_pdf(self, name=None):
        if name is None:
            name = self.dataflow.name
        self._dotGraph.write_pdf(name + '.pdf')

    def write_jpeg(self, name=None):
        if name is None:
            name = self.dataflow.name
        self._dotGraph.write_jpeg(name + '.jpeg')


file_path_bs = "simpl_BlackScholes.tur"
# file_path_jpeg = "../../experimentations/indus/JPEG2000.tur"
dataflow = read_tur_file(file_path_bs)
# dataflow = get_csdf_into_sdf(dataflow)
d = Dot(dataflow)
d.write_pdf("test")
