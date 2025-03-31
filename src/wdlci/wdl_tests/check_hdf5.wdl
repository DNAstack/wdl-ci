version 1.0

# Validate input HDF5 files
# Input type: HDF5/H5AD/H5

task check_hdf5 {
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

		if ! h5ls ~{validated_output} &>/dev/null; then
			err "Validated HDF5: [~{basename(validated_output)}] is not valid; check format"
			exit 1
		else
			if ! h5ls ~{current_run_output} &>/dev/null; then
				err "Current run HDF5: [~{basename(current_run_output)}] is not valid"
				exit 1
			else
				echo "Current run HDF5: [~{basename(current_run_output)}] is valid"

				validated_output_hdf5=$(h5ls ~{validated_output})
				current_output_hdf5=$(h5ls ~{current_run_output})
				if [[ "$validated_output_hdf5" == "$current_output_hdf5" ]]; then
					echo "Objects match in HDF5:
						Expected output: [$validated_output_hdf5]
						Current run output: [$current_output_hdf5]"
				else
					err "Objects do not match in HDF5:
						Expected output: [$validated_output_hdf5]
						Current run output: [$current_output_hdf5]"
					exit 1
				fi
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
