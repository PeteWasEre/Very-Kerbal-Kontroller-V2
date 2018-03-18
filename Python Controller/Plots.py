# Adapted from original work by github user marioferpa --> https://github.com/marioferpa/krpcscripts

from matplotlib.colors import ListedColormap
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D, proj3d
import numpy as np
from math import radians, degrees

from Utilities import si_val


# Plot setup

class Launchplot:
    def __init__(self):

        self.fig = plt.figure(figsize=(7, 7), facecolor="black")
        self.ax1 = self.fig.add_subplot(111)

        self.xar, self.yar = 0, 0
        self.xlim = 10
        self.ylim = 10

        # Gradient

        self.colormap = ListedColormap(np.loadtxt("kerbin_colormap.txt") / 255, N=256)  # made with http://jdherman.github.io/colormap/
        gradient = np.linspace(0, 10, 256)
        self.Z = np.zeros(shape=(256, 2))
        n = 255

        for item in gradient:
            self.Z[n] = np.array([item, item])
            n -= 1

        self.data_x = np.array(0)
        self.data_y = np.array(0)

        self.rts = False
        self.run_plot = False
        self.h_distance = 0

        self.start_coord = np.array((0, 0))

        plt.xlim(-2, self.xlim)
        plt.ylim(0, self.ylim)

        self.ax1.imshow(self.Z, cmap=self.colormap, interpolation="bicubic", extent=[-2, self.xlim, 0, self.ylim])
        self.ax1.set_title("Launch Trajectory", fontsize=24, color="blue", fontweight="bold")
        self.ax1.set_xlabel("Horizontal distance (km)", fontsize=20, color="blue", fontweight="bold")
        self.ax1.set_ylabel("Altitude (km)", fontsize=20, color="blue", fontweight="bold")
        self.ax1.tick_params(color="blue", labelcolor="blue", labelsize=16)

        for spine in self.ax1.spines.values():
            spine.set_edgecolor("blue")

        self.fig.canvas.draw()

    def animate(self, vessel, position, altitude):

        if str(vessel.situation) == "VesselSituation.pre_launch" or str(vessel.situation) == "VesselSituation.landed":
            self.xar, self.yar = 0, 0
            self.start_coord = np.array(position)
            self.h_distance = 0
            self.xlim = 10
            self.ylim = 10
            self.rts = True

        elif self.rts:
            self.run_plot = True
            self.rts = False

        if self.run_plot:
            if altitude >= vessel.orbit.body.atmosphere_depth:
                self.run_plot = False

            self.h_distance = (np.linalg.norm(position - self.start_coord) * (2. * np.pi * vessel.orbit.body.equatorial_radius) / 360.) / 1000  # km
            self.xar = np.append(self.xar, self.h_distance)
            self.yar = np.append(self.yar, altitude / 1000)

            # PLOT
            if self.xlim - self.h_distance < 5:
                self.xlim += 20
                self.ylim += 10

            if self.ylim - altitude / 1000 < 5:
                self.ylim += 10
                self.xlim += 10

            self.ax1.clear()  # can I move this to the start of the loop?
            self.ax1.plot(self.xar, self.yar, color="white", linewidth="5")

            plt.xlim(-2, self.xlim)
            plt.ylim(0, self.ylim)

            self.ax1.imshow(self.Z, cmap=self.colormap, interpolation="bicubic", extent=[-2, self.xlim, 0, self.ylim])
            self.ax1.set_title("Launch Trajectory", fontsize=24, color="blue", fontweight="bold")
            self.ax1.set_xlabel("Horizontal distance (km)", fontsize=20, color="blue", fontweight="bold")
            self.ax1.set_ylabel("Altitude (km)", fontsize=20, color="blue", fontweight="bold")
            self.ax1.tick_params(color="blue", labelcolor="blue", labelsize=16)

            for spine in self.ax1.spines.values():
                spine.set_edgecolor("blue")

            self.fig.canvas.draw()


class Orbitplot:
    def __init__(self):
        self.fig = plt.figure(figsize=(7, 9), facecolor="black")
        self.ax1 = self.fig.add_subplot(211, polar=True, axisbg="black")
        self.ax2 = self.fig.add_subplot(212, projection='3d', axisbg="black", aspect="equal")

        # set the starting view mode
        self.mode = 2

    def animate(self, vessel, periapsis, eccentricity, ecc_anom, incl, argPe):
        # Calculate data used in both modes
        pr = vessel.orbit.body.equatorial_radius

        inclination = incl + np.pi
        q = periapsis + pr  # periapsis radius
        a = q / (1 - eccentricity)  # semi major axis
        ap = 2 * a - q  # aperiapsis radius

        theta = np.linspace(0, 2 * np.pi, 181)
        r = (a * (1 - eccentricity ** 2)) / (1 + eccentricity * np.cos(theta))

        true_anom = 2 * np.arctan2(np.sqrt(1 + eccentricity) * np.sin(ecc_anom / 2), np.sqrt(1 - eccentricity) * np.cos(ecc_anom / 2))
        r_vess = (a * (1 - eccentricity ** 2)) / (1 + eccentricity * np.cos(true_anom))

        # Plot 1
        if self.mode is not 1:
            # clear the plot and reset its properties
            self.ax1.clear()
            self.ax1.set_theta_offset(np.pi)
            self.ax1.axis("off")
            self.ax1.set_title("Orbit - Planar View", fontsize=24, color="blue", fontweight="bold")

            #  plot the planet
            circle = plt.Circle((0, 0), pr, transform=self.ax1.transData._b, color="grey", alpha=1)
            self.ax1.add_artist(circle)
            self.ax1.annotate(vessel.orbit.body.name,
                              xy=(.5, .5),
                              xycoords='axes fraction',
                              horizontalalignment='center',
                              verticalalignment='center',
                              color="white",
                              size=24
                              )

            # set the plot axis limits
            self.ax1.set_rlim(ap * 1.25)

            # plot the orbit
            self.ax1.plot(theta, r, color="blue", lw=3)

            # plot PE and AP
            self.ax1.plot([0], [q], "D", color="white", markersize=7)
            self.ax1.annotate("Pe = " + si_val(periapsis, 2) + "m",
                              xy=(0, q),  # theta, radius
                              xytext=(-5, -5),  # fraction, fraction
                              textcoords='offset points',
                              horizontalalignment='right',
                              verticalalignment='bottom',
                              color="white"
                              )

            self.ax1.plot([np.pi], [ap], "D", color="white", markersize=7)
            self.ax1.annotate("Ap = " + si_val(ap - pr, 2) + "m",
                              xy=(np.pi, ap),  # theta, radius
                              xytext=(5, 5),  # fraction, fraction
                              textcoords='offset points',
                              horizontalalignment='left',
                              verticalalignment='bottom',
                              color="white"
                              )

            # plot the current position
            self.ax1.plot([true_anom], [r_vess], ".", color="red", markersize=20)

        # plot 2
        if self.mode is not 0:
            self.ax2.clear()
            self.ax2.axis("off")
            self.ax2.set_title("Orbit - Oblique View", fontsize=24, color="blue", fontweight="bold")

            # Adjustment of the axes, so that they all have the same span:
            for axis in 'xyz':
                getattr(self.ax2, 'set_{}lim'.format(axis))((-a, a))

            r2 = (a * (1 - eccentricity ** 2)) / (1 + eccentricity * np.cos(theta + np.asanyarray(argPe) - np.pi / 2))

            xo = r2 * np.cos(theta)
            y2 = r2 * np.sin(theta)
            zo = np.zeros(181)

            inclination = incl

            x2 = xo * np.cos(inclination) + zo * np.sin(inclination)
            # y2 = yo
            z2 = -xo * np.sin(inclination) + zo * np.cos(inclination)

            # Set up marker points
            # coord index, label, marker, colours (in RGBA) and sizes
            # AN and Dn
            # These are simple as we have rotated our orbit so the An is at +Y
            node_label = [(45, "An", "^", [0, 1, 0, 1], 10),
                          (135, "Dn", "v", [0, 1, 0, 1], 10)]

            # Pe and Ap
            # These are then calculated from An using argPe, and opposite to that point.
            i_pe = (45 + int(degrees(argPe) / 2)) % 180
            i_ap = (i_pe + 90) % 180

            node_label.append((i_pe, "Pe", "D", [1, 1, 1, 1], 10))
            node_label.append((i_ap, "Ap", "D", [1, 1, 1, 1], 10))

            # Vessel
            i_ve = (i_pe + int(degrees(true_anom) / 2)) % 180
            node_label.append((i_ve, "", "o", [1, 0, 0, 1], 10))

            self.ax2.plot(x2, y2, z2)

            for i in range(len(node_label)):
                xl, yl, _ = proj3d.proj_transform(x2[node_label[i][0]], y2[node_label[i][0]], z2[node_label[i][0]], self.ax2.get_proj())
                self.ax2.plot([x2[node_label[i][0]]], [y2[node_label[i][0]]], [z2[node_label[i][0]]], node_label[i][2], c=node_label[i][3], markersize=node_label[i][4])
                self.ax2.annotate(node_label[i][1],
                                  xy=(xl, yl),
                                  xytext=(5, 5),  # fraction, fraction
                                  textcoords='offset points',
                                  horizontalalignment='left',
                                  verticalalignment='bottom',
                                  color="white"
                                  )

            # add the planet
            t1, t2 = np.mgrid[0.0:np.pi:150j, 0.0:2.0 * np.pi:150j]
            xp = pr * np.sin(t1) * np.cos(t2)
            yp = pr * np.sin(t1) * np.sin(t2)
            zp = pr * np.cos(t1)

            self.ax2.plot_surface(xp, yp, zp, color="grey", edgecolor="none")

        self.fig.canvas.draw()

    def switch(self):
        self.mode = (self.mode + 1) % 3
        print(self.mode)

        if self.mode == 0:
            self.fig.delaxes(self.ax1)
            self.fig.delaxes(self.ax2)
            self.ax1 = self.fig.add_subplot(111, polar=True, axisbg="black")

        elif self.mode == 1:
            self.fig.delaxes(self.ax1)
            # self.fig.delaxes(self.ax2)  # only because switch order is fixed.
            self.ax2 = self.fig.add_subplot(111, projection='3d', axisbg="black", aspect="equal")

        else:
            # self.fig.delaxes(self.ax1)    # only because switch order is fixed.
            self.fig.delaxes(self.ax2)
            self.ax1 = self.fig.add_subplot(211, polar=True, axisbg="black")
            self.ax2 = self.fig.add_subplot(212, projection='3d', axisbg="black", aspect="equal")
