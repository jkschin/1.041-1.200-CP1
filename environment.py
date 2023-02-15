import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.backends.backend_agg as agg
import matplotlib.pyplot as plt
import pygame
import random
import time
from car import Car


total_simulations = 15
pixel_meters_ratio = 0.04
ppu = 30
simulation_time = 30
dt = 0.1
time_threshold = 15


class Environment:
    def __init__(self):

        # initialize the interfaces
        pygame.init()
        pygame.display.set_caption("1.041/1.200 CP1")
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.exit = False
        infoObject = pygame.display.Info()
        print("[INFO] Created infoObject...")
        self.screen_width = infoObject.current_w
        print("[INFO] Set screen_width...")

    def init_graphs(self):

        # initialize the graphs
        figure_svd, axis_svd = plt.subplots()
        figure_fvd, axis_fvd = plt.subplots()
        axis_svd.plot([], [])
        axis_fvd.plot([], [])

        axis_svd.set(xlabel='Density (veh/m)', ylabel='Speed (m/s)',
                     title='Speed vs Density')

        axis_fvd.set(xlabel='Density (veh/m)', ylabel='Flow (veh/s)',
                     title='Flow vs Density')

        axis_svd.grid()
        axis_fvd.grid()

        return figure_svd, figure_fvd, axis_svd, axis_fvd

    def plot_graph(figure):

        # Generate figure structure on the canvas
        canvas = agg.FigureCanvasAgg(figure)
        canvas.draw()
        renderer = canvas.get_renderer()
        raw_data = renderer.tostring_rgb()

        size = canvas.get_width_height()

        return raw_data, size

    def run(self, args):
        screen_width = self.screen_width
        # load car image for the visualization
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "car.png")
        car_image = pygame.image.load(image_path)
        file_fd = open("flow-density-data", "a")
        file_sd = open("flow-speed-data", "a")

        if args.run_idm:
            model = 'IDM'
        elif args.run_custom:
            model = 'Custom'
        else:
            model = 'Test'

        svd_x_axis = []
        svd_y_axis = []
        fvd_x_axis = []
        fvd_y_axis = []

        # Load the graphs
        figure_svd, figure_fvd, axis_svd, axis_fvd = Environment.init_graphs(self)
        vehicle_counts = [1,2,2,4,7,11,15,18,21,24,30,40,60,80,99]
        simulation_count = 0
        while simulation_count < total_simulations:

            simulation_count += 1
            time_elapsed = 0
            cars = []

            num_vehicles = vehicle_counts[simulation_count-1]

            for x in range(0, num_vehicles):
                if x == 0:
                    cars.append(Car((screen_width / ppu - (48 / ppu)) * 0.75, 2, x, screen_width))
                else:
                    cars.append(Car(cars[x - 1].position.x - random.uniform(1, 2), 2, x, screen_width))

            reference_position_x = cars[len(cars) - 1].position.x - 1
            road_length = max((screen_width / ppu - (48 / ppu)) * 0.25,
                              (abs(screen_width / ppu - (48 / ppu)) - reference_position_x))
            density = num_vehicles / (road_length * pixel_meters_ratio)

            flow = 0
            sum_velocity = 0
            velocity_count = 0

            while simulation_time > time_elapsed:

                time_elapsed += dt
                car_previous_positions_x = []

                # Update each vehicle's status
                for x in range(0, len(cars)):
                    if x == 0:
                        car_previous_positions_x.append(cars[0].position.x)
                        cars[x].car_following_model(dt, cars[len(cars) - 1], cars[min(len(cars)-1, 1)], reference_position_x, model)
                    elif x < len(cars) -1:
                        car_previous_positions_x.append(cars[x].position.x)
                        cars[x].car_following_model(dt, cars[x - 1], cars[x + 1], reference_position_x, model)
                    else:
                        car_previous_positions_x.append(cars[x].position.x)
                        cars[x].car_following_model(dt, cars[x - 1], cars[0], reference_position_x, model)

                if time_elapsed > time_threshold:
                    for y in range(0, len(cars)):
                        if cars[y].position.x < car_previous_positions_x[y]:
                            flow += 1

                if time_elapsed > time_threshold:
                    for car in cars:
                        sum_velocity += car.velocity.x
                        velocity_count += 1

                # Event queue for the simulation
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.exit = True
                    if event.type == pygame.KEYDOWN:
                        # quite the simulation whenever a key is pressed
                        pygame.quit()

                # Draw the simulation interface
                self.screen.fill((255, 255, 255))
                rotated = pygame.transform.rotate(car_image, 0)

                for x in range(0, len(cars)):
                    self.screen.blit(rotated, cars[x].position * ppu)

                screen = pygame.display.get_surface()

                # Draw the svd graph
                svd_raw_data, svd_size = Environment.plot_graph(figure_svd)
                surf = pygame.image.fromstring(svd_raw_data, svd_size, "RGB")
                screen.blit(surf, (screen_width / 9, 180))

                # Draw the fvd graph
                fvd_raw_data, fvd_size = Environment.plot_graph(figure_fvd)
                surf = pygame.image.fromstring(fvd_raw_data, fvd_size, "RGB")
                screen.blit(surf, (screen_width / 2, 180))

                # Add text to interface
                font = pygame.font.Font('freesansbold.ttf', 16)
                text = font.render('[INFO] : Running %s simulation No : %d '
                                   'with %d vehicle/s '
                                   % (model, simulation_count, num_vehicles),
                                   True, (0, 0, 0), (255, 255, 255))
                text_quit = font.render('[X] : Press any key to quit the simulation.',
                                   True, (0, 0, 0), (255, 255, 255))

                textRect = text.get_rect()
                textRectQuit = text_quit.get_rect()
                textRect.center = (400, 25)
                textRectQuit.center = (400, 50)
                screen.blit(text, textRect)
                screen.blit(text_quit, textRectQuit)

                # Update interface
                pygame.display.flip()

            # collect data relevant for plotting
            avg_velocity = sum_velocity / velocity_count

            svd_x_axis.append(density)
            svd_y_axis.append(avg_velocity)
            axis_svd.scatter(svd_x_axis, svd_y_axis)
            file_sd.write(str(density) + "," + str(avg_velocity) + "\n")

            fvd_x_axis.append(density)
            flow_real = flow / (simulation_time - time_threshold)
            fvd_y_axis.append(flow_real)
            axis_fvd.scatter(fvd_x_axis, fvd_y_axis)
            file_fd.write(str(density) + "," + str(flow_real) + "\n")

        # Save the two graphs as pngs
        figure_svd.savefig('figure_svd.png')
        figure_fvd.savefig('figure_fvd.png')
        file_fd.close()
        file_sd.close()
        # wait 5 seconds before exit
        time.sleep(5)
