*
.option brief=1
.lib "/Users/virantha/dev/circuitbrew/skywater-pdk-libs-sky130_fd_pr/models/sky130.lib.spice" tt
.option brief=0
.option scale=1e-6
*xm1 d1 g1 0 0 sky130_fd_pr__nfet_01v8_lvt w=1 l=0.5
*vgs g1 0 dc=0.9
*vds d1 0 dc=0.9
*---------------------------------------
.temp ${temp}
.param voltage=${voltage}
.option post

${circuit}

xmain ${main_type_name}

.tran 1p 10n

.end

