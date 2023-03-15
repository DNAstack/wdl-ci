version 1.0

# Check if file is tab-delimited
# Input type: File

task check_tab_delimited {
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
		
		if ! awk '{exit !/\t/}' "${dir_path}/$(basename ~{validated_output} .gz)"; then
			err "Validated file: [~{basename(validated_output)}] is not tab-delimited"
			exit 1
		else
			if awk '{exit !/\t/}' "${dir_path}/$(basename ~{current_run_output} .gz)"; then
				echo "File: [~{basename(current_run_output)}] is tab-delimited"
			else
				err "File: [~{basename(current_run_output)}] is not tab-delimited"
				exit 1
			fi
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
