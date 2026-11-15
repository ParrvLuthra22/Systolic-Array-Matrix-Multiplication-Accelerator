IVERILOG = iverilog -g2012
RTL = rtl

.PHONY: pe array buf out ctrl top seq test vectors report diagram clean

test: pe array buf out ctrl top seq

pe:
	$(IVERILOG) -o sim_pe $(RTL)/pe.v tb/tb_pe.v
	vvp sim_pe

array:
	$(IVERILOG) -o sim_array $(RTL)/pe.v $(RTL)/systolic_array.v tb/tb_array.v
	vvp sim_array

buf:
	$(IVERILOG) -o sim_buf $(RTL)/input_buffer.v tb/tb_input_buffer.v
	vvp sim_buf

out:
	$(IVERILOG) -o sim_out $(RTL)/output_collector.v tb/tb_output_collector.v
	vvp sim_out

ctrl:
	$(IVERILOG) -o sim_ctrl $(RTL)/controller.v tb/tb_controller.v
	vvp sim_ctrl

top:
	$(IVERILOG) -o sim_top $(RTL)/pe.v $(RTL)/systolic_array.v $(RTL)/input_buffer.v \
		$(RTL)/output_collector.v $(RTL)/controller.v $(RTL)/systolic_top.v tb/tb_top.v
	vvp sim_top

seq:
	$(IVERILOG) -o sim_seq $(RTL)/sequential_mac.v tb/tb_sequential.v
	vvp sim_seq

vectors:
	python3 model/golden_model.py

report:
	python3 docs/report/build_report.py

diagram:
	python3 docs/make_block_diagram.py

clean:
	rm -f sim_* *.vcd
