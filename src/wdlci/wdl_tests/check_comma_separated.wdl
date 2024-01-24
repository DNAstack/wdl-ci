version 1.0

# Check if file is comma-separated
# Input type: File or GZ file

task check_comma_separated {
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

		if gzip -t ~{current_run_output}; then
			gzip -d ~{current_run_output} ~{validated_output}
		fi

		# Validated dir path in input block vs. command block is different
		validated_dir_path=$(dirname ~{validated_output})
		current_dir_path=$(dirname ~{current_run_output})

		if ! awk '{exit !/,/}' "${validated_dir_path}/$(basename ~{validated_output} .gz)"; then
			err "Validated file: [~{basename(validated_output)}] is not comma-separated"
			exit 1
		else
			if awk '{exit !/,/}' "${current_dir_path}/$(basename ~{current_run_output} .gz)"; then
				echo "Current run file: [~{basename(current_run_output)}] is comma-separated"
			else
				err "Current run file: [~{basename(current_run_output)}] is not comma-separated"
				exit 1
			fi
		fi
	>>>

	output {
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
