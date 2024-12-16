version 1.0

# Validate input json files
# Input type: JSON

task check_json {
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
			gzip -d -f ~{current_run_output} ~{validated_output}
		fi

		# Dir path in input block vs. command block is different
		validated_dir_path=$(dirname ~{validated_output})
		current_dir_path=$(dirname ~{current_run_output})

		if ! json_pp < "${validated_dir_path}/$(basename ~{validated_output} .gz)"; then
			err "Validated JSON: [~{basename(validated_output)}] is not valid; check schema"
			exit 1
		else
			if ! json_pp < "${current_dir_path}/$(basename ~{current_run_output} .gz)"; then
				err "Current run JSON: [~{basename(current_run_output)}] is not valid"
				exit 1
			else
				echo "Current run JSON: [~{basename(current_run_output)}] is valid"
			fi
		fi
	>>>

	output {
	}

	runtime {
		docker: "dnastack/dnastack-wdl-ci-tools:0.0.1"
		cpu: 1
		memory: "3.75 GB"
		disk: disk_size + " GB"
		disks: "local-disk " + disk_size + " HDD"
		preemptible: 1
	}
}
