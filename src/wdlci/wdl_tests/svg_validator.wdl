version 1.0

# Validate input SVG files
# Input type: SVG file

task svg_validator {
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

		if ! html5validator ~{validated_output} --skip-non-svg --ignore 'error: Element "path" is missing required attribute "d"'; then
			err "Validated SVG: [~{basename(validated_output)}] is invalid"
			exit 1
		else
			if ! html5validator ~{current_run_output} --skip-non-svg --ignore 'error: Element "path" is missing required attribute "d"'; then
				err "Current run SVG: [~{basename(current_run_output)}] is invalid"
				exit 1
			else
				echo "Current run SVG: [~{basename(current_run_output)}] is valid"
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
