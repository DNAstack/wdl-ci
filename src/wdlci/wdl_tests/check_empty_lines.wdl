version 1.0

# Check empty lines
# Input type: File

task check_empty_lines {
	input {
		File current_run_output
		File validated_output
	}

	Int disk_size = ceil(size(current_run_output, "GB") + size(validated_output, "GB") + 50)

	command <<<
		set -euo pipefail

		err() {
			message=$1

			echo -e "[ERROR] $message" >&2
		}

		dir_path=$(dirname ~{current_run_output})

		if gzip -t ~{current_run_output}; then
			gzip -d ~{current_run_output} ~{validated_output}
		fi

		#validated_output_empty_lines_count=$(grep -c "^$" "${dir_path}/$(basename ~{validated_output} .gz)")
		#current_run_output_empty_lines_count=$(grep -c "^$" "${dir_path}/$(basename ~{current_run_output} .gz)")

		if [[ $(grep -c "^$" "${dir_path}/$(basename ~{validated_output} .gz)") != $(grep -c "^$" "${dir_path}/$(basename ~{current_run_output} .gz)") ]]; then
			err "Empty lines present:
				Expected output: [$(grep -c "^$" "${dir_path}/$(basename ~{validated_output} .gz)")]
				Current run output: [$(grep -c "^$" "${dir_path}/$(basename ~{current_run_output} .gz)")]"
			exit 1
		else
			echo "No empty lines. Count: [$(grep -c "^$" "${dir_path}/$(basename ~{current_run_output} .gz)")]"
		fi
	>>>

	output {
		#Int rc = read_int("rc")
	}

	runtime {
		docker: "ubuntu:xenial"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
