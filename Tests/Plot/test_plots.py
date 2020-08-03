from numpy import linspace, sin, squeeze
from unittest import TestCase
from os.path import join
import matplotlib.pyplot as plt
from Tests import save_validation_path as save_path
import pytest

from pyleecan.Classes.Simu1 import Simu1

from pyleecan.Classes.Output import Output
from SciDataTool import DataTime, Data1D, DataLinspace, VectorField
from Tests import TEST_DATA_DIR
from pyleecan.Classes.ImportMatlab import ImportMatlab
from pyleecan.Classes.ImportData import ImportData
from pyleecan.Classes.ImportVectorField import ImportVectorField
from pyleecan.Classes.InputFlux import InputFlux

from pyleecan.Functions.load import load
from pyleecan.definitions import DATA_DIR

SCIM_006 = load(join(DATA_DIR, "Machine", "SCIM_006.json"))

simu = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)

mat_file_Br = join(TEST_DATA_DIR, "Plots/default_proj_Br.mat")
mat_file_time = join(TEST_DATA_DIR, "Plots/default_proj_time.mat")
mat_file_angle = join(TEST_DATA_DIR, "Plots/default_proj_angle.mat")
mat_file_MTr_freqs = join(TEST_DATA_DIR, "Plots/default_proj_MTr_freqs.mat")
mat_file_MTr_wavenumber = join(TEST_DATA_DIR, "Plots/default_proj_MTr_wavenumber.mat")
mat_file_MTr = join(TEST_DATA_DIR, "Plots/default_proj_MTr.mat")
mat_file_Br_cfft2 = join(TEST_DATA_DIR, "Plots/default_proj_Br_cfft2.mat")
mat_file_Brfreqs = join(TEST_DATA_DIR, "Plots/default_proj_Brfreqs.mat")
mat_file_Brwavenumber = join(TEST_DATA_DIR, "Plots/default_proj_Brwavenumber.mat")

# Read input files from Manatee
flux = ImportMatlab(mat_file_Br, var_name="XBr")
time = ImportMatlab(mat_file_time, var_name="timec")
Time = ImportData(field=time, unit="s", name="time")
angle = ImportMatlab(mat_file_angle, var_name="alpha_radc")
Angle = ImportData(field=angle, unit="rad", name="angle")
Br = ImportData(
    axes=[Time, Angle],
    field=flux,
    unit="T",
    name="Airgap radial flux density",
    normalizations={"space_order": 3},
    symbol="B_{rad}",
)
B = ImportVectorField(components={"radial": Br})

flux_FT = ImportMatlab(mat_file_Br_cfft2, var_name="Fwr")
freqs = ImportMatlab(mat_file_Brfreqs, var_name="freqs")
Freqs = ImportData(field=freqs, unit="Hz", name="freqs")
wavenumber = ImportMatlab(mat_file_Brwavenumber, var_name="orders")
Wavenumber = ImportData(field=wavenumber, unit="dimless", name="wavenumber")
Br_FT = ImportData(
    axes=[Freqs, Wavenumber],
    field=flux,
    unit="T",
    name="Airgap radial flux density",
    symbol="B_{rad}",
)
B_FT = ImportVectorField(components={"radial": Br_FT})

# Plot parameters
freq_max = 2000
r_max = 78


@pytest.mark.validation
class tests_plots(TestCase):
    def test_default_proj_Br_time_space(self):

        time_arr = squeeze(time.get_data())
        angle_arr = squeeze(angle.get_data())
        flux_arr = flux.get_data()

        simu = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)
        simu.mag = None
        simu.force = None
        simu.struct = None
        simu.input = InputFlux(B=B)
        out = Output(simu=simu)
        simu.run()

        out2 = Output(simu=simu)

        # Reduce to 1/3 period
        Br_reduced = flux_arr[0:672, 0:672]
        time_reduced = time_arr[0:672]
        angle_reduced = angle_arr[0:672]

        # Build the data objects
        Time2 = Data1D(
            name="time",
            unit="s",
            symmetries={"time": {"period": 3}},
            values=time_reduced,
        )
        Angle2 = Data1D(
            name="angle",
            unit="rad",
            symmetries={"angle": {"period": 3}},
            values=angle_reduced,
        )
        Br2 = DataTime(
            symbol="B_r",
            name="Airgap radial flux density",
            unit="T",
            symmetries={"time": {"period": 3}, "angle": {"period": 3}},
            axes=[Time2, Angle2],
            normalizations={},
            values=Br_reduced,
        )
        out2.mag.B = VectorField(
            name="Airgap flux density", symbol="B", components={"radial": Br2}
        )

        # Plot the result by comparing the two simulation (sym / no sym)
        plt.close("all")
        out.plot_A_time(
            "mag.B",
            is_fft=True,
            freq_max=freq_max,
            data_list=[out2.mag.B],
            legend_list=["Reference", "Periodic"],
            is_auto_ticks=False,
            save_path=join(save_path, "test_default_proj_Br_dataobj_period.png"),
        )

        out3 = Output(simu=simu)

        # Get linspace data
        t0 = time_arr[0]
        tf = time_arr[-1]
        deltat = time_arr[1] - time_arr[0]
        a0 = angle_arr[0]
        deltaa = angle_arr[1] - angle_arr[0]
        Na = len(angle_arr)

        # Build the data objects
        Time3 = DataLinspace(
            name="time",
            unit="s",
            symmetries={},
            initial=t0,
            final=tf + deltat,
            step=deltat,
            include_endpoint=False,
        )
        Angle3 = DataLinspace(
            name="angle",
            unit="rad",
            symmetries={},
            initial=a0,
            step=deltaa,
            number=Na,
            include_endpoint=False,
        )
        Br3 = DataTime(
            symbol="B_r",
            name="Airgap radial flux density",
            unit="T",
            symmetries={},
            axes=[Time3, Angle3],
            normalizations={"space_order": 3},
            values=flux_arr,
        )
        out3.mag.B = VectorField(
            name="Airgap flux density", symbol="B", components={"radial": Br3}
        )

        # Plot the result by comparing the two simulation (Data1D / DataLinspace)
        plt.close("all")
        out.plot_A_space(
            "mag.B",
            is_fft=True,
            is_spaceorder=True,
            r_max=r_max,
            data_list=[out3.mag.B],
            legend_list=["Reference", "Linspace"],
            is_auto_ticks=False,
            save_path=join(save_path, "test_default_proj_Br_dataobj_linspace.png"),
        )

        simu4 = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)
        simu4.input = InputFlux(B=B_FT)
        simu4.mag = None
        simu4.force = None
        simu4.struct = None
        simu4.input = InputFlux(B=B)
        out4 = Output(simu=simu4)
        simu4.run()
        out4.post.legend_name = "Inverse FT"

        # Plot the result by comparing the two simulation (direct / ifft)
        plt.close("all")
        out.plot_A_space(
            "mag.B",
            is_fft=True,
            r_max=r_max,
            data_list=[out4.mag.B],
            legend_list=["Reference", "Inverse FFT"],
            is_auto_ticks=False,
            save_path=join(save_path, "test_default_proj_Br_dataobj_ift.png"),
        )

        out5 = Output(simu=simu)

        # Get linspace data
        t0 = 0.01
        tf = 0.04
        Nt = 3000
        time5 = linspace(0.01, 0.04, 3000, endpoint=True)

        # Compute sine function
        Br5 = 0.2 * sin(375 * time5 - 1.5)

        # Build the data objects
        Time5 = DataLinspace(
            name="time",
            unit="s",
            symmetries={},
            initial=t0,
            final=tf,
            number=Nt,
            include_endpoint=True,
        )
        flux5 = DataTime(
            symbol="B_r",
            name="Airgap radial flux density",
            unit="T",
            symmetries={},
            axes=[Time5],
            normalizations={},
            values=Br5,
        )
        out5.mag.B = VectorField(
            name="Airgap flux density", symbol="B", components={"radial": flux5}
        )

        # Plot the result by comparing the two simulation (sym / no sym)
        plt.close("all")
        out.plot_A_time(
            "mag.B",
            data_list=[out5.mag.B],
            legend_list=["Br", "0.2sin(375t-1.5)"],
            is_auto_ticks=False,
            save_path=join(save_path, "test_default_proj_Br_compare.png"),
        )

    def test_default_proj_Br_cfft2(self):

        N_stem = 100

        simu = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)
        simu.input = InputFlux(B=B)
        simu.mag = None
        simu.force = None
        simu.struct = None
        simu.input = InputFlux(B=B)
        out = Output(simu=simu)
        simu.run()

        # Plot the result by comparing the two simulation (sym / no sym)
        plt.close("all")
        out.plot_A_cfft2(
            "mag.B",
            freq_max=freq_max,
            r_max=r_max,
            N_stem=N_stem,
            save_path=join(save_path, "test_default_proj_Br_dataobj_cfft2.png"),
        )

    def test_default_proj_surf(self):

        simu = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)
        simu.input = InputFlux(B=B_FT)
        simu.mag = None
        simu.force = None
        simu.struct = None
        simu.input = InputFlux(B=B)
        out = Output(simu=simu)
        simu.run()

        # Plot the result by comparing the two simulation (sym / no sym)
        plt.close("all")
        out.plot_A_surf(
            "mag.B",
            t_max=0.06,
            save_path=join(save_path, "test_default_proj_Br_surf_dataobj.png"),
        )

    def test_default_proj_fft2(self):

        simu = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)
        simu.input = InputFlux(B=B_FT)
        simu.mag = None
        simu.force = None
        simu.struct = None
        simu.input = InputFlux(B=B)
        out = Output(simu=simu)
        simu.run()

        # Plot the result by comparing the two simulation (sym / no sym)
        plt.close("all")
        out.plot_A_fft2(
            "mag.B",
            freq_max=500,
            r_max=20,
            save_path=join(save_path, "test_default_proj_Br_fft2_dataobj.png"),
        )

    def test_default_proj_time_space(self):

        simu = Simu1(name="EM_SCIM_NL_006", machine=SCIM_006)
        simu.input = InputFlux(B=B)
        simu.mag = None
        simu.force = None
        simu.struct = None
        simu.input = InputFlux(B=B)
        out = Output(simu=simu)
        simu.run()

        # Plot the result by comparing the two simulation (sym / no sym)
        plt.close("all")
        out.plot_A_time_space(
            "mag.B",
            freq_max=freq_max,
            r_max=r_max,
            is_auto_ticks=False,
            save_path=join(save_path, "test_default_proj_Br_time_space_dataobj.png"),
        )