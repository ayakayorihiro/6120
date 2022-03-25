if [ $# -ne 1 ]; then
    echo "USAGE: $0 BENCHMARKS_DIR"
    exit
fi


SCRIPT_DIR=$( cd $( dirname $0 ) && pwd )
BENCHMARKS_DIR=$1
OUT=${SCRIPT_DIR}/ayaka-licm-eval.csv

TMP_DIR=${SCRIPT_DIR}/eval
mkdir -p ${TMP_DIR}
reg_file=${TMP_DIR}/reg.txt
licm_file=${TMP_DIR}/licm.txt

echo "name,baseline,licm,%-improvement" >> ${OUT}
for benchmark in $( ls ${BENCHMARKS_DIR} | grep ".bril" | grep -v turnt | grep -v circle  | grep -v factors ); do
    benchmark_name=$( echo ${benchmark} | cut -d. -f1 )
    echo $benchmark_name
    args=$( grep "# ARGS" ${BENCHMARKS_DIR}/${benchmark} | cut -d' ' -f3- )
    # run regular version
    ( bril2json < ${BENCHMARKS_DIR}/${benchmark} | time brili -p $args ) &> ${reg_file}
    r_dyn_inst=$( grep "total_dyn_inst" ${reg_file} | cut -d' ' -f2 )
    r_time_in_sec=$( grep "user " ${reg_file} | cut -d'u' -f1 )
    # run licm version
    ( bril2json < ${BENCHMARKS_DIR}/${benchmark} | python3 ${SCRIPT_DIR}/licm.py | time brili -p $args ) &> ${licm_file}
    l_dyn_inst=$( grep "total_dyn_inst" ${licm_file} | cut -d' ' -f2 )
    l_time_in_sec=$( grep "user " ${licm_file} | cut -d'u' -f1 )
    if [[ "${r_dyn_inst}" != "" && "${r_dyn_inst}" != "0" && "${l_dyn_inst}" != "" && "${l_dyn_inst}" != "" ]]; then
        improv=$( echo "scale=3;  100 *((${r_dyn_inst} - ${l_dyn_inst})/${r_dyn_inst})" | bc -l)
    else
        improv=-1
    fi
    echo ${benchmark_name},${r_dyn_inst},${l_dyn_inst},${improv} >> ${OUT} # ,${r_time_in_sec},${l_time_in_sec}
done

rm -rf ${TMP_DIR}
