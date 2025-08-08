import { FaUpload } from "react-icons/fa"
import { useEffect } from "react"
import "aos/dist/aos.css"
import AOS from "aos"

const FormConverter = ({ setView, tabla, setFile, file, form, handleRowSelect, handleFormChange, handleConvert, downloadUrl, convertError, convertLoading }) => {
    useEffect(() => {
        AOS.init()
    }, [])

    return (
        <div data-aos="zoom-in-up" className="converter-flex-exact">
            {/* Panel izquierdo: Tabla de parámetros */}
            <div className="converter-table-panel-exact">
                <div className="converter-table-title-row">
                    <div className="converter-table-title">CUT PARAMETERS</div>
                    <div className="converter-table-title-underline" />
                </div>
                <div className="converter-table-headers-row">
                    <div className="converter-table-header">MATERIAL</div>
                    <div className="converter-table-header">CURRENT</div>
                    <div className="converter-table-header">WIDTH (mm)</div>
                    <div className="converter-table-header">SPEED CUT (mm/s)</div>
                </div>
                <div className="converter-table-list converter-table-scrollable">
                    {tabla.map((row, i) => (
                        <div className="converter-table-row" key={i} onClick={() => handleRowSelect(row)}>
                            <div className="converter-table-cell converter-table-cell-material">{row['Material']}</div>
                            <div className="converter-table-cell">{row['Current (A)']} A</div>
                            <div className="converter-table-cell">{row['Thickness (mm)']}</div>
                            <div className="converter-table-cell">{row['Cutting speed (mm/s)']}</div>
                        </div>
                    ))}
                </div>
                <button style={{ marginTop: '28px' }} className="converter-back-btn" onClick={() => setView('select')}>
                    ← Back
                </button>
            </div>
            {/* Panel derecho: Formulario de conversión */}
            <div className="converter-form-panel-exact">
                <div className="converter-form-title">CONVERT .DXF TO INFORM II</div>
                <div className="converter-form-subtitle">(SELECT A .DXF FILE TO CONVERT TO ROBOT YASKAWA LANGUAGE)</div>
                <div className="converter-form-file-row">
                    <label className="converter-form-file-btn">
                        SELECT YOUR FILE
                        <input type="file" accept=".dxf" style={{ display: 'none' }} onChange={e => setFile(e.target.files[0])} />
                    </label>
                    <div className="converter-form-file-name">{file ? file.name : ''}</div>
                </div>

                {/* Formulario con el botón dentro */}
                <form onSubmit={handleConvert} className="converter-form-fields-grid">
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">MATERIAL</label>
                        <input className="converter-form-input" name="Material" value={form['Material']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">J SPEED</label>
                        <input type="number" className="converter-form-input" name="Velocidad J" value={form['Velocidad J']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">CURRENT</label>
                        <input type="number" className="converter-form-input" name="Corriente (A)" value={form['Corriente (A)']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">Z POSITION</label>
                        <input type="number" className="converter-form-input" name="Z" value={form['Z']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">WIDTH</label>
                        <input type="number" className="converter-form-input" name="Espesor (mm)" value={form['Espesor (mm)']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">USER FRAME</label>
                        <input type="number" className="converter-form-input" name="User Frame" value={form['User Frame']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">SPEED CUT</label>
                        <input type="number" className="converter-form-input" name="Velocidad corte (mm/s)" value={form['Velocidad corte (mm/s)']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">TOOL</label>
                        <input type="number" className="converter-form-input" name="Tool" value={form['Tool']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">KERF</label>
                        <input type="number" className="converter-form-input" name="Kerf" value={form['Kerf']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">PASSES</label>
                        <input type="number" className="converter-form-input" name="Pasadas" value={form['Pasadas']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">DEPTH CUT</label>
                        <input type="number" className="converter-form-input" name="Profundidad de Corte" value={form['Profundidad de Corte']} onChange={handleFormChange} />
                    </div>
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">ARC SPEED</label>
                        <input type="number" className="converter-form-input" name="Velocidad de Arco" value={form['Velocidad de Arco']} onChange={handleFormChange} />
                    </div>
                    {/* <div className="converter-form-field-group">
                        <label className="converter-form-label">OUTPUT TOOL</label>
                        <select
                            name='Numero de Salida'
                            className="converter-form-input"
                            value={form['Numero de Salida']}
                            onChange={handleFormChange}
                        >
                            <option value="9">Plasma</option>
                            <option value="1">Dremel</option>
                        </select>
                    </div> */}
                    <div className="converter-form-field-group">
                        <label className="converter-form-label">TYPE TOOL</label>
                        <select
                            name='Uso'
                            className="converter-form-input"
                            value={form['Uso']}
                            onChange={handleFormChange}
                        >
                            <option value="0">Plasma</option>
                            <option value="1">Dremel</option>
                        </select>
                    </div>

                    <button className="converter-form-submit-btn" type="submit" disabled={convertLoading}>
                        CONVERT & UPLOAD <FaUpload style={{ marginLeft: 10, marginBottom: -3 }} />
                    </button>
                </form>

                {convertError && <div className="converter-form-error">{convertError}</div>}
                {downloadUrl && (
                    <a href={downloadUrl} download={file ? file.name.replace(/\.[^.]+$/, '.JBI') : 'programa.jbi'} className="converter-form-download-link">Descargar archivo .JBI</a>
                )}
            </div>
        </div>
    )
}

export default FormConverter
