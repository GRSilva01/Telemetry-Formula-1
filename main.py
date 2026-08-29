import fastf1
import fastf1.plotting
import fastf1.utils
import matplotlib.pyplot as plt

fastf1.Cache.enable_cache('cache')

#variavel para definir a sessao a ser vista
session = fastf1.get_session(2024, 'Brazil', 'Q')

#linha necessaria para carregar os dados
session.load()

ver_lap = session.laps.pick_driver('VER').pick_fastest()
nor_lap = session.laps.pick_driver('NOR').pick_fastest()
delta_time, ref_tel, compare_tel = fastf1.utils.delta_time(ver_lap, nor_lap)

ver_telemetry = ver_lap.get_car_data().add_distance()
nor_telemetry = nor_lap.get_car_data().add_distance()

ver_color = fastf1.plotting.get_team_color('Red Bull Racing', session=session)
nor_color = fastf1.plotting.get_team_color('McLaren', session=session)

plt.style.use('dark_background')
fig, ax = plt.subplots(4, 1, figsize=(13, 9), sharex=True,
                        gridspec_kw={'height_ratios': [3, 1, 1, 1]})

plt.subplots_adjust(hspace=0.08)


# Grafico 1 de velocidade
ax[0].plot(ref_tel['Distance'], delta_time, color='white', linewidth=1.5, label='Delta (VER vs NOR)')
ax[0].axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax[0].set_ylabel('Delta (s)')
ax[0].grid(True, alpha=0.2)
ax[0].legend(loc='upper left')
ax[0].set_title(f"Telemetria Comparativa: VER ({ver_lap['LapTime']}) vs NOR ({nor_lap['LapTime']}) - Interlagos 2024", fontsize=12)

ax[1].plot(ver_telemetry['Distance'], ver_telemetry['Speed'], color=ver_color, label='VER')
ax[1].plot(nor_telemetry['Distance'], nor_telemetry['Speed'], color=nor_color, label='NOR')
ax[1].set_ylabel('Speed (km/h)')
ax[1].grid(True, alpha=0.2)
ax[1].legend(loc='lower right')

# Grafico 2 de acelerador
ax[2].plot(ver_telemetry['Distance'], ver_telemetry['Throttle'], color=ver_color)
ax[2].plot(nor_telemetry['Distance'], nor_telemetry['Throttle'], color=nor_color)
ax[2].set_ylabel('Throttle %')
ax[2].set_yticks([0, 50, 100])
ax[2].grid(True, alpha=0.2)

# Grafico 3 de freio
ax[3].plot(ver_telemetry['Distance'], ver_telemetry['nGear'], color=ver_color, drawstyle='steps-post')
ax[3].plot(nor_telemetry['Distance'], nor_telemetry['nGear'], color=nor_color, drawstyle='steps-post')
ax[3].set_ylabel('Gear')
ax[3].set_xlabel('Distance (m)')
ax[3].set_yticks(range(1, 9))
ax[3].set_ylim(0.5, 8.5)
ax[3].grid(True, alpha=0.2)

plt.show()